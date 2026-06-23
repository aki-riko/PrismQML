# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""FluentQML Window Classes - Python版窗口类

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
from typing import Optional, List, Dict, Any, Callable, Type, Union
from PySide6.QtCore import QObject, Signal, Slot, Property, QUrl, Qt
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication, QIcon
from pathlib import Path

from ..core.engine import EngineManager
from ..providers import get_svg_provider
from ..core.logger import warning, info, error, debug

# ==================== 窗口类型枚举 ====================


class WindowType(IntEnum):
    """窗口类型枚举

    与QML侧 FluentEnums.windowType 对应：
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
        page_builder: Optional[Callable] = None,
    ):
        """
        Args:
            text: 导航项文本
            icon: 图标名称（Icon）
            page_class: 页面类（需要接受parent参数）
            page_builder: 页面构建函数（接受parent参数，返回页面实例）
        """
        self.text = text
        self.icon = icon
        self.page_class = page_class
        self.page_builder = page_builder
        self.page_getter = None
        self._page_instance = None


# ==================== 窗口基类 ====================


from ._window_builder import WindowBuilderMixin
from ._page_manager import PageManagerMixin


class WindowCore(QObject, WindowBuilderMixin, PageManagerMixin):
    """FluentQML窗口基类"""

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

        self._window_type = window_type
        self._engine: Optional[QQmlApplicationEngine] = None
        self._window: Optional[QQuickWindow] = None
        self._content_area: Optional[QQuickItem] = None
        # ⚠️ 启动时序: 子类常在 __init__ 里调 setWindowTitle/setMicaEffectEnabled 等,
        # 此时 _window 还没创建,直接 setProperty 会被静默吞掉。这两个字典缓存早期调用,
        # _create_window 完成后由 _apply_pending_state 统一刷给 QML。
        self._pending_props: Dict[str, Any] = {}
        self._pending_calls: List[tuple] = []   # [(method_name, qvariant_arg), ...]

        self._title = "FluentQML App"
        self._width = 1200
        self._height = 800
        self._icon = ""
        self._icon_colored = True

        self._nav_items: List[NavigationItem] = []
        self._bottom_nav_items: List[NavigationItem] = []
        self._current_index = 0

        self._pages: Dict[int, Any] = {}
        # 从配置读取懒加载设置 Read lazy loading from config
        from ..config import getConfigManager

        self._lazy_loading = getConfigManager().lazyLoading
        self._user_card: Optional[Dict[str, str]] = None

        # ==================== Splash 启动画面 ====================
        # 默认开启: _create_window 末尾会自动实例化 SplashScreen.qml 并挂到 QML
        # 根对象的 _splashInstance,首屏内容真正加载完成时由框架
        # (WindowsBar/Split/Filled -> NavigationWindowCore._dismissSplashWhenReady)
        # 自动淡出。不想要的项目调 setSplashEnabled(False) 关掉即可。
        self._splash_enabled = True
        # 文本/图标默认留空,_create_splash 时回退到窗口自身的 icon/title。
        self._splash_icon = ""        # 图标路径或图标名,空=用 windowIcon
        self._splash_title = ""       # 标题,空=用 windowTitle
        self._splash_subtitle = ""    # 副标题/加载文字,空=不显示
        self._splash_instance: Optional[QQuickItem] = None

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

        # Set application-level icon for taskbar 设置应用程序级别图标（任务栏）
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

    def _setAppIcon(self, icon: str):
        """Set application icon for taskbar 设置任务栏图标

        Args:
            icon: Icon path (supports file path, qrc:/, :/ formats) 图标路径
        """
        if not icon:
            return

        # Resolve icon path 解析图标路径
        icon_path = icon
        if icon.startswith("qrc:/"):
            icon_path = icon[4:]  # Remove "qrc:" prefix, keep ":/xxx"
        elif icon.startswith("file:///"):
            icon_path = icon[8:]  # Remove "file:///" prefix
        elif not icon.startswith(":/"):
            # Local file path 本地文件路径
            icon_path = str(Path(icon).resolve())

        # Create and set QIcon 创建并设置QIcon
        app = QGuiApplication.instance()
        if app:
            # SVG needs special handling SVG需要特殊处理
            if icon_path.lower().endswith(".svg"):
                from PySide6.QtSvg import QSvgRenderer
                from PySide6.QtGui import QPixmap, QPainter
                from PySide6.QtCore import QSize

                renderer = QSvgRenderer(icon_path)
                if renderer.isValid():
                    # Render at multiple sizes for taskbar 为任务栏渲染多种尺寸
                    qicon = QIcon()
                    for size in [16, 24, 32, 48, 64, 128, 256]:
                        pixmap = QPixmap(QSize(size, size))
                        pixmap.fill(Qt.GlobalColor.transparent)
                        painter = QPainter(pixmap)
                        renderer.render(painter)
                        painter.end()
                        qicon.addPixmap(pixmap)
                    app.setWindowIcon(qicon)
            else:
                app.setWindowIcon(QIcon(icon_path))

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
        """添加子界面

        Args:
            interface: 页面类或页面实例，None表示功能项
                - 传入类：懒加载模式，在切换时创建实例
                - 传入实例：立即使用该实例
            icon: 图标名称（Icon）或图片路径
            text: 导航项文本
            position: 位置 "top" 或 "bottom"
            selectedIcon: 选中时的图标（可选）
            selectable: 是否可选中（False表示功能项，只发送回调不切换页面）

        Returns:
            导航项索引

        Example:
            # 传入类（懒加载）
            window.addPage(ButtonPage, "CursorClick", "按钮")

            # 传入实例
            home_page = HomePage()
            window.addPage(home_page, "Home", "主页")

            # 功能项（点击只发送回调，不切换页面）
            window.addPage(None, "Person", "用户", position="bottom", selectable=False)
        """
        # 判断是类还是实例还是函数
        is_class = isinstance(interface, type)
        is_callable = callable(interface) and not is_class
        is_instance = interface is not None and not is_class and not is_callable

        if is_instance:
            # 传入的是实例，直接使用
            item = NavigationItem(text, icon, page_class=None)
            item._page_instance = interface  # 直接保存实例
        elif is_callable:
            # 传入的是getter工厂函数
            item = NavigationItem(text, icon, page_class=None)
            item.page_getter = interface
        else:
            # 传入的是类，懒加载
            item = NavigationItem(text, icon, page_class=interface)

        item.selected_icon = selectedIcon
        item.selectable = selectable  # 标记是否可选中
        if position == "bottom":
            self._bottom_nav_items.append(item)
            return len(self._bottom_nav_items) - 1
        else:
            self._nav_items.append(item)
            return len(self._nav_items) - 1

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

    def setUserCard(
        self,
        avatar: str = "",
        title: str = "",
        subtitle: str = "",
        position: str = "bottom",
    ):
        """设置用户卡片/头像

        Args:
            avatar: 头像图片路径或图标名称
            title: 用户名/标题
            subtitle: 副标题（如邮箱）
            position: 位置 "top" 或 "bottom"

        Example:
            window.setUserCard(avatar="Person", title="用户名", subtitle="user@example.com")
        """
        self._user_card = {
            "avatar": avatar,
            "title": title,
            "subtitle": subtitle,
            "position": position,
        }

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
            # 1) QML 侧立即切换: 让侧边栏 selected 状态 + stackedWidget index
            #    立刻响应, 即使 Python 内容容器还没填好,导航栏视觉先到位
            self._switch_to_index(index)
            # 2) Python 侧页面: 已创建直接结束;未创建走异步加载有 loading
            if self._lazy_loading and index not in self._pages:
                self._start_async_page_load(index)
            self.currentIndexChanged.emit(index)

    def currentIndex(self) -> int:
        return self._current_index

    # ==================== 窗口生命周期 ====================

    def show(self):
        """显示窗口"""
        if self._window is None:
            self._create_window()

        if self._window:
            self._window.show()
            # 设置为当前活动窗口
            WindowCore._current_window_instance = self

            # Python侧懒加载：启动时只创建首页，其他页面在切换时创建
            if self._lazy_loading:
                if self._nav_items or self._bottom_nav_items:
                    self._ensure_page_created(0)
            else:
                # 非懒加载：预创建所有页面
                total = len(self._nav_items) + len(self._bottom_nav_items)
                for i in range(total):
                    self._ensure_page_created(i)

            # ✅ 2026-05-25: Mica 初始化交给 QML 端的 nativeHookReady 信号,
            # 那里会等 _dwmDelayTimer 跑完(shadow + NativeWindow.attach 都会发
            # SWP_FRAMECHANGED 重置 DWM backdrop)再设。Python 这里不再单独 timer,
            # 避免抢早调用被 FRAMECHANGED 清掉,导致"启动看不到 Mica 必须开关一次"。

    def hide(self):
        if self._window:
            self._window.hide()

    def isVisible(self) -> bool:
        """转发到 QQuickWindow.isVisible — Resource monitor 和外部代码常用 isVisible 检查
        窗口是否可见; 提供给跟 QWidget 行为对齐的代码使用"""
        return bool(self._window and self._window.isVisible())

    def activateWindow(self):
        """转发到 QQuickWindow.requestActivate — 跟 QWidget API 对齐;
        托盘点击 / 外部唤起主窗口时把窗口提到前台并获得焦点"""
        if self._window:
            self._window.requestActivate()

    def showNormal(self):
        """转发到 QQuickWindow.showNormal — 跟 QWidget API 对齐;
        从最小化/最大化恢复为普通窗口状态"""
        if self._window:
            self._window.showNormal()

    def showMinimized(self):
        """转发到 QQuickWindow.showMinimized — 跟 QWidget API 对齐"""
        if self._window:
            self._window.showMinimized()

    def showMaximized(self):
        """转发到 QQuickWindow.showMaximized — 跟 QWidget API 对齐"""
        if self._window:
            self._window.showMaximized()

    def isMaximized(self) -> bool:
        """通过 QQuickWindow.visibility 判定 — 跟 QWidget API 对齐;
        QWindow.Visibility.Maximized 对应最大化状态"""
        if not self._window:
            return False
        return self._window.visibility() == QQuickWindow.Visibility.Maximized

    def isMinimized(self) -> bool:
        """通过 QQuickWindow.visibility 判定 — 跟 QWidget API 对齐"""
        if not self._window:
            return False
        return self._window.visibility() == QQuickWindow.Visibility.Minimized

    def raise_(self):
        """转发到 QQuickWindow.raise_ — 跟 QWidget API 对齐;
        把窗口提升到同级窗口栈最前"""
        if self._window:
            self._window.raise_()

    def windowFlags(self):
        """转发到 QWindow.flags — 跟 QWidget API 对齐"""
        if not self._window:
            return Qt.WindowFlags()
        return self._window.flags()

    def setWindowFlags(self, flags):
        """转发到 QWindow.setFlags — 跟 QWidget API 对齐;
        QWidget 改 flags 后需要 show() 重新生效,QWindow.setFlags 行为一致"""
        if self._window:
            self._window.setFlags(flags)

    def setMinimumSize(self, width: int, height: int):
        """转发到 QWindow.setMinimumSize — 跟 QWidget API 对齐;
        Initialization manager / 主窗口构造期会调,QWindow 未创建时缓存到字面量,
        _create_window 拼 QML 时读 self._min_width/_min_height"""
        from PySide6.QtCore import QSize
        self._min_width = width
        self._min_height = height
        if self._window:
            self._window.setMinimumSize(QSize(width, height))

    def setMaximumSize(self, width: int, height: int):
        """转发到 QWindow.setMaximumSize — 跟 QWidget API 对齐"""
        from PySide6.QtCore import QSize
        self._max_width = width
        self._max_height = height
        if self._window:
            self._window.setMaximumSize(QSize(width, height))

    def repaint(self):
        """转发到 QQuickWindow.update — 跟 QWidget API 对齐;
        QWidget.repaint 是同步立即重绘,QQuickWindow 没有同步 API,
        update() 是请求下一帧重绘 — 休眠唤醒 / power monitor 触发用足够"""
        if self._window:
            self._window.update()

    def close(self):
        if self._window:
            self._window.close()
            self.windowClosed.emit()

    def addOverlay(self, widget: Any):
        """添加覆盖层组件（如Drawer、Dialog等）到窗口层级

        Args:
            widget: 要添加的覆盖层组件

        Note:
            覆盖层组件会被添加到窗口的contentItem，覆盖所有内容。
            适用于Drawer、MessageBox、Dialog等需要全屏覆盖的组件。
        """
        if self._window and hasattr(widget, "_qml_item") and widget._qml_item:
            widget._qml_item.setParentItem(self._window.contentItem())

    def getContentItem(self) -> Optional[QQuickItem]:
        """获取窗口的contentContainer，用于添加覆盖层组件"""
        if self._window:
            # 查找contentContainer（WindowCore中定义的内容区域）
            from PySide6.QtQuick import QQuickItem

            content_container = self._window.findChild(QQuickItem, "contentContainer")
            if content_container:
                return content_container
            # 回退到contentItem
            return self._window.contentItem()
        return None


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
            # 连接导航切换信号
            try:
                self._window.currentPageChanged.connect(self._on_nav_changed)
            except AttributeError as e:
                warning(f"导航信号连接失败: {e}")
