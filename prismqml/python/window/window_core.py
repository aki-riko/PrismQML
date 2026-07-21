# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML Window Classes - Python版窗口类

提供统一的Window API，通过window_type参数选择窗口风格：
- WindowType.BAR (1): 紧凑侧边导航（默认）
- WindowType.SPLIT (0): 展开式侧边导航
- WindowType.FILLED (2): 填充式分割窗口

懒加载机制：
- 懒加载完全由Python侧管理，QML侧只负责动画和UI渲染
- 启动时只创建首页，其他页面在切换时按需创建
- 支持分批创建（ScrollArea._deferred_queue），避免大量组件一次性创建导致卡顿
- Loading动画使用QML的_pythonLoading覆盖层，保持流畅

使用示例：
    from prismqml import Window, WindowType

    # 紧凑侧边导航（默认）
    window = Window()

    # 展开式侧边导航
    window = Window(window_type=WindowType.SPLIT)

    # 填充式分割窗口
    window = Window(window_type=WindowType.FILLED)

    window.setWindowTitle("My App")
    window.resize(1200, 800)
    window.addPage(ButtonPage, "CursorClick", "按钮")
    window.show()
"""

from enum import IntEnum
from typing import Optional, List, Dict, Any, Type, Union
from PySide6.QtCore import QObject, Signal, Slot, Property, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtGui import QGuiApplication, QIcon

from ..core.engine import EngineManager
from ..core.logger import warning, exception, debug

# ==================== 窗口类型枚举 ====================


class WindowType(IntEnum):
    """窗口类型枚举

    与QML侧 PrismEnums.windowType 对应：
    - SPLIT (0): 展开式侧边导航
    - BAR (1): 紧凑侧边导航（默认）
    - FILLED (2): 填充式分割窗口
    """

    SPLIT = 0  # type_fluent - 展开式侧边导航
    BAR = 1  # type_ms - 紧凑侧边导航（默认）
    FILLED = 2  # type_filled_split - 填充式分割窗口


# 类型名称映射（用于QML）— IntEnum 不允许非成员类属性
_WINDOW_TYPE_QML_NAMES = {
    WindowType.SPLIT: "WindowsSplit",  # _internal/WindowsSplit.qml
    WindowType.BAR: "WindowsBar",  # _internal/WindowsBar.qml (default)
    WindowType.FILLED: "WindowsFilled",  # _internal/WindowsFilled.qml
}


# ==================== 导航项 ====================


class NavigationItem:
    """导航项配置"""

    def __init__(
        self,
        text: str,
        icon: str = "",
        page_class: Optional[Type] = None,
    ):
        """
        Args:
            text: 导航项文本
            icon: 图标名称（Icon）
            page_class: 页面类（需要接受parent参数）
        """
        self.text = text
        self.icon = icon
        self.page_class = page_class
        self.page_getter = None
        self._page_instance = None


def _make_navigation_item(
    interface: Optional[Union[Type, Any]], icon: str, text: str
) -> NavigationItem:
    is_class = isinstance(interface, type)
    is_callable = callable(interface) and not is_class
    is_instance = interface is not None and not is_class and not is_callable
    if is_instance:
        item = NavigationItem(text, icon, page_class=None)
        item._page_instance = interface
        return item
    if is_callable:
        item = NavigationItem(text, icon, page_class=None)
        item.page_getter = interface
        return item
    return NavigationItem(text, icon, page_class=interface)


class WindowCloseEvent:
    """Cancellable close event passed to WindowCore.closeEvent."""

    def __init__(self):
        self._accepted = True

    @property
    def accepted(self) -> bool:
        return self._accepted

    @accepted.setter
    def accepted(self, value: bool):
        self._accepted = bool(value)

    def accept(self):
        self._accepted = True

    def ignore(self):
        self._accepted = False

    def isAccepted(self) -> bool:
        return self._accepted


# ==================== 窗口基类 ====================


from ._window_builder import WindowBuilderMixin
from ._window_init import initialize_splash_state, initialize_window_state
from ._page_manager import PageManagerMixin
from ._window_compat import WindowCompatMixin
from ._window_show import (
    ensure_initial_pages,
    invoke_optional_startup_hook,
    make_show_profile,
    show_window_root,
)


class WindowCore(QObject, WindowBuilderMixin, PageManagerMixin, WindowCompatMixin):
    """PrismQML窗口基类"""

    # 信号
    currentIndexChanged = Signal(int)
    windowClosed = Signal()

    # 类变量：当前活动窗口
    _current_window_instance: Optional["WindowCore"] = None

    @classmethod
    def get_current_window(cls) -> Optional["WindowCore"]:
        """获取当前活动窗口"""
        return cls._current_window_instance

    def __init__(
        self, window_type: int = WindowType.BAR, parent: Optional[QObject] = None
    ):
        """初始化窗口

        Args:
            window_type: 窗口类型，使用 WindowType 枚举
                - WindowType.SPLIT (0): 展开式侧边导航
                - WindowType.BAR (1): 紧凑侧边导航（默认）
                - WindowType.FILLED (2): 填充式分割窗口
            parent: 父对象
        """
        super().__init__(parent)
        initialize_window_state(self, window_type)
        # 从配置读取懒加载设置 Read lazy loading from config
        from ..config import getConfigManager

        self._lazy_loading = getConfigManager().lazyLoading
        initialize_splash_state(self)

    # ==================== 窗口属性 ====================

    # ⚠️ 内部 helper: setProperty / invokeMethod 在 _window 创建前调用都会被 Qt 静默吞掉。
    # 所有公开 setter 必须通过这两个 helper,而不是直接 if self._window: ...
    # _create_window 末尾会调 _apply_pending_state 把缓存刷给 QML。
    def _set_window_property(self, key: str, value: Any):
        """设置 QML 根属性。_window 未就绪时缓存到 _pending_props。"""
        if self._window:
            self._window.setProperty(key, value)
        else:
            self._pending_props[key] = value

    def _invoke_window_method(self, method: str, qvariant_arg: Any):
        """调用 QML 根方法。_window 未就绪时缓存到 _pending_calls。"""
        if self._window:
            from PySide6.QtCore import QMetaObject, Q_ARG
            QMetaObject.invokeMethod(self._window, method, Q_ARG("QVariant", qvariant_arg))
        else:
            self._pending_calls.append((method, qvariant_arg))

    def _apply_pending_state(self):
        """_create_window 后 apply 早期被缓存的属性/方法调用。"""
        if not self._window:
            return
        for k, v in self._pending_props.items():
            self._window.setProperty(k, v)
        self._pending_props.clear()
        if self._pending_calls:
            from PySide6.QtCore import QMetaObject, Q_ARG
            for method, arg in self._pending_calls:
                QMetaObject.invokeMethod(self._window, method, Q_ARG("QVariant", arg))
            self._pending_calls.clear()

    def setWindowTitle(self, title: str):
        self._title = title
        self._set_window_property("windowTitle", title)

    def windowTitle(self) -> str:
        return self._title

    def resize(self, width: int, height: int):
        self._width = width
        self._height = height
        if self._window:
            self._window.setWidth(width)
            self._window.setHeight(height)
        # 注: width/height 是 _create_window 拼 QML 时的字面量,无需 pending —
        # _window 未创建时改 self._width/_height 即可,create 时会读到新值

    def setWindowIcon(self, icon: str, colored: bool = True):
        """设置窗口图标（同时设置标题栏和任务栏图标）

        Args:
            icon: 图标路径或图标名称
            colored: 是否为彩色图标（默认True，保留原始颜色）
        """
        # Normalize Windows backslashes to forward slashes for QML
        # 将Windows反斜杠转换为正斜杠供QML使用
        icon = icon.replace("\\", "/")
        self._icon = icon
        self._icon_colored = colored

        # Window creation writes windowIcon into QML, which syncs the taskbar icon.
        # Before the QML window exists, avoid rendering the same SVG twice.
        if self._window:
            self._setAppIcon(icon)

        self._set_window_property("windowIcon", icon)
        self._set_window_property("windowIconColored", colored)

    def windowIcon(self) -> QIcon:
        """获取窗口图标

        Returns:
            QIcon: 窗口图标
        """
        app = QGuiApplication.instance()
        if app:
            return app.windowIcon()
        return QIcon()

    def _setAppIcon(self, icon: str) -> None:
        """Set the shared application icon. 设置共享应用图标。"""
        from ..core.window_helper import get_window_helper

        get_window_helper().setAppIcon(icon)

    def setMicaEffectEnabled(self, enabled: bool):
        """设置云母效果

        Args:
            enabled: 是否启用云母效果

        ⚠️ Python 这里只 setProperty 写到 QML 端,**不直接调 DWM API**。
        DWM 调用统一交给 QML 的 nativeHookReady 信号 (NavigationWindowCore.qml),
        那里会等 shadow / NativeWindow.attach (都会发 SWP_FRAMECHANGED 重置
        DWM backdrop) 完成后再设。
        在那之前 setProperty 触发的 onMicaEnabledChanged 也会试着调 DWM,但即便
        被 FRAMECHANGED 清掉,最终的 nativeHookReady 还会以正确状态再设一次,
        保证启动时一定生效,无需手动开关。

        子类 __init__ 期间调用本方法时 _window 还没创建,值会被 _set_window_property
        缓存到 _pending_props,_create_window 完成时 _apply_pending_state 自动 flush。
        """
        self._set_window_property("micaEnabled", enabled)

    def isMicaEffectEnabled(self) -> bool:
        """获取云母效果状态"""
        from .mica_window import get_mica_manager

        return get_mica_manager().micaEnabled

    def setLanguage(self, lang: str):
        """设置界面语言

        Args:
            lang: 语言代码，如 "zh_CN", "en", "ja" 等
        """
        self._invoke_window_method("setLanguage", lang)

    def setLazyLoading(self, enabled: bool):
        self._lazy_loading = enabled

    # ==================== Splash 启动画面 ====================

    def setSplashEnabled(self, enabled: bool):
        """开关启动画面(默认开启)。

        必须在 show()/_create_window() 之前调用才生效 —— splash 在
        _create_window 末尾一次性创建,创建后此开关不再读取。

        Args:
            enabled: False 则不显示启动画面
        """
        self._splash_enabled = enabled

    def showSplash(self, icon: str = "", title: str = "", subtitle: str = ""):
        """自定义启动画面的图标/标题/副标题并确保开启。

        不调用此方法时 splash 默认开启,图标取 windowIcon、标题取 windowTitle。
        同样需在 show()/_create_window() 之前调用。

        Args:
            icon: 图标路径或图标名(空=用 windowIcon)
            title: 标题(空=用 windowTitle)
            subtitle: 副标题/加载文字(空=不显示)
        """
        self._splash_enabled = True
        if icon:
            self._splash_icon = icon
        if title:
            self._splash_title = title
        if subtitle:
            self._splash_subtitle = subtitle

    # ==================== 导航项 ====================

    def addPage(
        self,
        interface: Optional[Union[Type, Any]],
        icon: str,
        text: str,
        position: str = "top",
        selectedIcon: str = "",
        selectable: bool = True,
    ) -> int:
        """添加页面或功能项并返回所选导航列表中的局部索引。

        Args:
            interface: 页面类、页面工厂、页面实例或 None 功能项
            icon: 图标名称或图片路径
            text: 导航项文本
            position: "top" 或 "bottom"
            selectedIcon: 选中态图标
            selectable: 是否允许选中

        Returns:
            top 或 bottom 列表内的局部索引
        """
        item = _make_navigation_item(interface, icon, text)
        item.selected_icon = selectedIcon
        item.selectable = selectable
        items = self._bottom_nav_items if position == "bottom" else self._nav_items
        items.append(item)
        return len(items) - 1

    def removePage(self, interface: Type):
        """移除子界面

        Args:
            interface: 要移除的页面类
        """
        # 从导航项中查找并移除
        for items in [self._nav_items, self._bottom_nav_items]:
            for item in items[:]:
                if item.page_class == interface:
                    items.remove(item)
                    break

    def navigateTo(self, interface: Type):
        """切换到指定界面

        Args:
            interface: 页面类
        """
        for i, item in enumerate(self._nav_items):
            if item.page_class == interface:
                self.setCurrentIndex(i)
                return

    def setCurrentIndex(self, index: int):
        """切换到指定页面

        QML 侧立即切换 (侧边栏选中态、stackedWidget 索引同步),
        Python 侧页面如未创建则异步创建 + loading 动画, 与侧边栏点击
        (`_on_nav_changed`) 一致。

        之前同步走 `_ensure_page_created` 阻塞主线程 100~150ms,
        用户感知为'卡顿'。
        """
        total_count = len(self._nav_items) + len(self._bottom_nav_items)
        if 0 <= index < total_count:
            self._current_index = index
            self._discard_page_prewarm(index)
            if self._is_page_prewarming(index):
                self._mark_foreground_page_load_started(index)
                self._start_loading_overlay(index)
            else:
                # 1) QML 侧立即切换: 让侧边栏 selected 状态 + stackedWidget index
                #    立刻响应, 即使 Python 内容容器还没填好,导航栏视觉先到位
                self._switch_to_index(index)
            # 2) Python 侧页面: 已创建直接结束;未创建走异步加载有 loading
            if (
                self._lazy_loading
                and index not in self._pages
                and not self._is_page_prewarming(index)
            ):
                self._start_async_page_load(index)
            self.currentIndexChanged.emit(index)

    def currentIndex(self) -> int:
        return self._current_index

    # ==================== 窗口生命周期 ====================

    def show(self):
        """显示窗口"""
        profile = make_show_profile(debug)
        if not show_window_root(self, profile):
            return
        WindowCore._current_window_instance = self
        invoke_optional_startup_hook(self, "_begin_startup_page_guard")
        ensure_initial_pages(self, profile)
        # Keep Mica initialization in QML nativeHookReady; no Python timer here.
        # Mica 初始化继续由 QML nativeHookReady 负责；此处不新增 Python timer。

    def _find_content_area(self):
        """查找内容区域"""
        if self._window is None:
            return

        # 查找contentFrame或stackedWidget（复用已有方法）
        stack = self._find_child_by_name("stack")
        if stack is None:
            # 尝试其他名称
            stack = self._find_child_by_name("contentArea")

        if stack:
            self._content_area = stack
        else:
            # 如果找不到，使用窗口的contentItem
            self._content_area = self._window.contentItem()

    def _connect_signals(self):
        """连接QML信号到Python"""
        if self._window:
            try:
                self._window.closeRequested.connect(self._on_close_requested)
            except AttributeError as e:
                warning(f"关闭请求信号连接失败: {e}")

            # 连接导航切换信号
            try:
                self._window.currentPageChanged.connect(self._on_nav_changed)
            except AttributeError as e:
                warning(f"导航信号连接失败: {e}")

    def _on_close_requested(self):
        """Bridge QML closeRequested to the QWidget-compatible closeEvent hook."""
        if not self._window:
            return

        event = WindowCloseEvent()
        try:
            self.closeEvent(event)
        except Exception as exc:
            exception(
                "WindowCore.closeEvent failed: "
                f"{type(exc).__name__}: {exc}"
            )
            event.ignore()

        try:
            self._window.setProperty("closeRequestAccepted", event.isAccepted())
        except RuntimeError as exc:
            exception(
                "WindowCore.closeRequestAccepted write failed: "
                f"{type(exc).__name__}: {exc}"
            )
