# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""
FluentQML 应用入口类 FluentQML Application Entry

提供统一的应用管理API，封装 QApplication 常用操作。
"""

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication

from ..core.engine import EngineManager
from .fluent_window import Window, WindowCore, WindowType


class App:
    """
    FluentQML应用入口 FluentQML Application Entry

    统一的应用管理类，封装QApplication常用API。

    Example:
        ```python
        from fluentqml import App, Window

        app = App()
        window = app.create_window()
        window.show()
        app.exec()
        ```
    """

    _instance: "App" = None

    def __init__(self, argv: List[str] = None):
        from ..config import applyDpiScale
        from ..core import (
            installDwmSyncFilter,
            register_types,
            install_qt_message_handler,
        )

        # 单例检查
        if App._instance is not None:
            raise RuntimeError(
                "App already exists. Use App.instance() to get the existing instance."
            )
        App._instance = self

        # 设置DPI
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        applyDpiScale()

        # 安装Qt消息处理器（将QML日志重定向到logger）
        install_qt_message_handler()

        # 创建应用
        self._app = QApplication(argv or [])
        installDwmSyncFilter()

        # 创建引擎
        self._engine = QQmlApplicationEngine()
        EngineManager.set_engine(self._engine)

        # 安装异步孵化控制器: 让 asynchronous Loader(StackedWidget 懒加载)分帧
        # 切片实例化, 避免切到未加载页时单帧建整棵页面树阻塞 GUI 线程(与导航
        # 指示器动画抢帧)造成掉帧。
        from ..core.incubation import install_incubation_controller
        install_incubation_controller(self._engine)

        # 注册所有provider（包括ScreenEyedropperManager等）
        register_types(self._engine)

        self._windows: List[WindowCore] = []

    # ==================== 类方法 Class Methods ====================

    @classmethod
    def instance(cls) -> "App":
        """获取App单例 Get App singleton"""
        if cls._instance is None:
            raise RuntimeError("App not created yet. Create App() first.")
        return cls._instance

    @classmethod
    def _reset(cls) -> None:
        """重置单例状态（仅供测试使用） Reset singleton state (for testing only)"""
        cls._instance = None

    @classmethod
    def quit(cls) -> None:
        """退出应用 Quit application"""
        QApplication.quit()

    @classmethod
    def exit(cls, returnCode: int = 0) -> None:
        """退出应用并返回指定代码 Exit with return code"""
        QApplication.exit(returnCode)

    @classmethod
    def processEvents(cls) -> None:
        """处理待处理的事件 Process pending events"""
        QApplication.processEvents()

    @classmethod
    def clipboard(cls):
        """获取剪贴板 Get clipboard"""
        return QApplication.clipboard()

    @classmethod
    def screens(cls) -> list:
        """获取所有屏幕 Get all screens"""
        return QApplication.screens()

    @classmethod
    def primaryScreen(cls):
        """获取主屏幕 Get primary screen"""
        return QApplication.primaryScreen()

    @classmethod
    def activeWindow(cls):
        """获取当前活动窗口 Get active window"""
        return QApplication.activeWindow()

    @classmethod
    def focusWidget(cls):
        """获取当前焦点控件 Get focus widget"""
        return QApplication.focusWidget()

    @classmethod
    def setApplicationName(cls, name: str) -> None:
        """设置应用名称 Set application name"""
        QApplication.setApplicationName(name)

    @classmethod
    def applicationName(cls) -> str:
        """获取应用名称 Get application name"""
        return QApplication.applicationName()

    @classmethod
    def setApplicationVersion(cls, version: str) -> None:
        """设置应用版本 Set application version"""
        QApplication.setApplicationVersion(version)

    @classmethod
    def applicationVersion(cls) -> str:
        """获取应用版本 Get application version"""
        return QApplication.applicationVersion()

    @classmethod
    def setOrganizationName(cls, name: str) -> None:
        """设置组织名称 Set organization name"""
        QApplication.setOrganizationName(name)

    @classmethod
    def organizationName(cls) -> str:
        """获取组织名称 Get organization name"""
        return QApplication.organizationName()

    @classmethod
    def topLevelWidgets(cls) -> list:
        """获取所有顶层 widget Get all top-level widgets"""
        return QApplication.topLevelWidgets()

    @classmethod
    def allWidgets(cls) -> list:
        """获取所有 widget Get all widgets"""
        return QApplication.allWidgets()

    @classmethod
    def mouseButtons(cls):
        """获取当前鼠标按键状态 Get current mouse buttons state"""
        return QApplication.mouseButtons()

    @classmethod
    def keyboardModifiers(cls):
        """获取当前键盘修饰键状态 Get current keyboard modifiers state"""
        return QApplication.keyboardModifiers()

    @classmethod
    def installNativeEventFilter(cls, filter_obj) -> None:
        """安装原生事件过滤器 Install native event filter"""
        app = QApplication.instance()
        if app is not None:
            app.installNativeEventFilter(filter_obj)

    @classmethod
    def removeNativeEventFilter(cls, filter_obj) -> None:
        """移除原生事件过滤器 Remove native event filter"""
        app = QApplication.instance()
        if app is not None:
            app.removeNativeEventFilter(filter_obj)

    @classmethod
    def setFont(cls, font) -> None:
        """设置应用全局字体 Set application font"""
        QApplication.setFont(font)

    @classmethod
    def font(cls):
        """获取应用全局字体 Get application font"""
        return QApplication.font()

    @classmethod
    def setHighDpiScaleFactorRoundingPolicy(cls, policy) -> None:
        """设置高DPI缩放策略（必须在 App 创建前调用）Set high DPI rounding policy (must call before App creation)"""
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(policy)

    # ==================== 实例方法 Instance Methods ====================

    def create_window(self, window_type: int = WindowType.BAR) -> Window:
        """创建窗口 Create window

        Args:
            window_type: 窗口类型，使用 WindowType 枚举
                - WindowType.SPLIT (0): 展开式侧边导航
                - WindowType.BAR (1): 紧凑侧边导航（默认）
                - WindowType.FILLED (2): 填充式分割窗口

        Returns:
            Window 实例
        """
        window = Window(window_type=window_type)
        self._windows.append(window)
        return window

    @property
    def engine(self) -> QQmlApplicationEngine:
        """获取QML引擎 Get QML engine"""
        return self._engine

    @property
    def windows(self) -> List[WindowCore]:
        """获取所有窗口 Get all windows"""
        return self._windows

    @property
    def qapp(self) -> QApplication:
        """获取底层 QApplication 实例 Get underlying QApplication.

        显式逃生口 — 当某个 QApplication API 没被门面方法覆盖、或第三方
        库要求传 QApplication 实例时使用. 大多数情况直接 `app.xxx(...)`
        即可,会通过 `__getattr__` 自动转发.

        Escape hatch when an API isn't surfaced on the facade or a third-
        party lib requires a raw QApplication. Most of the time
        `app.xxx(...)` works directly via `__getattr__` forwarding.
        """
        return self._app

    def exec(self) -> int:
        """运行应用 Run application"""
        return self._app.exec()

    # ==================== 自动转发 Auto-forwarding ====================
    # 任何未在本类显式定义的属性/方法,都透传到底层 QApplication.
    # 这覆盖了所有未来新增的 QApplication API、信号 (aboutToQuit /
    # lastWindowClosed 等),以及不常用但偶尔需要的 setAttribute /
    # setQuitOnLastWindowClosed / setWindowIcon / aboutToQuit 等.
    #
    # __getattr__ 只在正常属性查找失败时才被调用,所以已显式定义的
    # classmethod / property 不会被遮蔽.
    def __getattr__(self, name: str):
        # 拒绝转发私有/dunder属性 — 避免 _app 未初始化时触发递归,
        # 也避免把 __reduce__ / __getstate__ 等 pickle 钩子误转发.
        if name.startswith("_"):
            raise AttributeError(
                f"{type(self).__name__!r} has no attribute {name!r}"
            )
        try:
            app = object.__getattribute__(self, "_app")
        except AttributeError:
            raise AttributeError(
                f"App not fully initialized; cannot forward {name!r} to QApplication"
            ) from None
        return getattr(app, name)


