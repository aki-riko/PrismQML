# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
PrismQML 应用入口类 PrismQML Application Entry

提供统一的应用管理API，封装 QApplication 常用操作。
"""

import os
from typing import TYPE_CHECKING, List, Optional, Union

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication

from ..core.engine import EngineManager
from ..core.input_focus_filter import (
    install_input_focus_filter,
    reset_input_focus_filter,
)
from ..core.utils import QML_XHR_ALLOW_FILE_READ_ENV
from ._application_icon_runtime import (
    ApplicationIconMixin,
    apply_application_icon_to_window,
    configure_initial_application_icon,
    initialize_application_icon_state,
)

if TYPE_CHECKING:
    from .fluent_window import Window
    from .window_core import WindowCore

_DEFAULT_WINDOW_TYPE = 1
_MISSING_ENVIRONMENT = object()


def _validate_task_shutdown_timeout(timeout_ms: Optional[int]) -> None:
    if timeout_ms is None:
        return
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int):
        raise TypeError("task_shutdown_timeout_ms must be an int or None")
    if timeout_ms < 0:
        raise ValueError("task_shutdown_timeout_ms must be non-negative or None")


def _initialize_app_state(owner, task_shutdown_timeout_ms: Optional[int]) -> None:
    """Initialize fields before fallible Qt startup. 在可能失败的 Qt 启动前初始化字段。"""
    _validate_task_shutdown_timeout(task_shutdown_timeout_ms)
    owner._app = None
    owner._engine = None
    owner._owns_app = False
    owner._input_filter_started = False
    owner._dwm_filter_started = False
    owner._engine_publish_started = False
    owner._task_shutdown_timeout_ms = task_shutdown_timeout_ms
    owner._windows = []
    owner._updater = None
    initialize_application_icon_state(owner)


def _prepare_app_environment(allow_qml_file_read: bool) -> None:
    """Prepare process-wide Qt settings. 准备进程级 Qt 设置。"""
    from ..config import applyDpiScale
    from ..core import configure_qml_environment, install_qt_message_handler

    configure_qml_environment(allow_qml_file_read)
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    applyDpiScale()
    install_qt_message_handler()


def _create_qt_application(owner, argv: List[str]) -> None:
    """Create QApplication and install global filters. 创建应用并安装全局过滤器。"""
    from ..core import installDwmSyncFilter

    owner._owns_app = QApplication.instance() is None
    owner._app = QApplication(argv or [])
    owner._input_filter_started = True
    install_input_focus_filter(owner._app)
    owner._dwm_filter_started = True
    installDwmSyncFilter()


def _create_qml_engine(owner) -> None:
    """Create and fully register the QML engine. 创建并完整注册 QML 引擎。"""
    from ..core import register_types
    from ..core.incubation import install_incubation_controller

    owner._engine = QQmlApplicationEngine()
    owner._engine_publish_started = True
    EngineManager.set_engine(owner._engine)
    install_incubation_controller(owner._engine)
    register_types(owner._engine)


def _run_app_cleanup(label: str, action) -> None:
    """Run one rollback action without masking startup failure. 执行回滚且不遮蔽启动异常。"""
    try:
        action()
    except Exception as exc:
        from ..core.logger import exception

        exception(f"App {label} cleanup failed 清理失败: {type(exc).__name__}: {exc}")


def _delete_qt_object(value) -> None:
    """Delete one live Shiboken-owned Qt object. 删除存活的 Qt 对象。"""
    import shiboken6

    if value is not None and shiboken6.isValid(value):
        shiboken6.delete(value)


def _delete_remaining_qml_windows() -> None:
    """Delete every QML window while QApplication is still alive. 在应用存活时销毁全部 QML 窗口。"""
    import shiboken6

    for window in tuple(QGuiApplication.topLevelWindows()):
        if shiboken6.isValid(window):
            window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def _clear_current_window_reference() -> None:
    """Drop the process-wide active window reference. 清除进程级活动窗口引用。"""
    from .window_core import WindowCore

    WindowCore._current_window_instance = None


def _restore_qml_environment(previous_value) -> None:
    """Restore the caller's QML XHR setting. 恢复调用方 QML XHR 设置。"""
    if previous_value is _MISSING_ENVIRONMENT:
        os.environ.pop(QML_XHR_ALLOW_FILE_READ_ENV, None)
    else:
        os.environ[QML_XHR_ALLOW_FILE_READ_ENV] = previous_value


def _rollback_app_initialization(owner, previous_qml_environment) -> None:
    """Rollback a partially initialized App. 回滚部分初始化的 App。"""
    from ..core.shadow import reset_dwm_sync_filter

    if owner._input_filter_started:
        _run_app_cleanup("input filter", reset_input_focus_filter)
    if owner._engine_publish_started and EngineManager._engine is owner._engine:
        _run_app_cleanup("engine bindings", EngineManager.reset)
    if owner._dwm_filter_started:
        _run_app_cleanup("DWM filter", reset_dwm_sync_filter)
    _run_app_cleanup("QML engine", lambda: _delete_qt_object(owner._engine))
    if owner._owns_app:
        _run_app_cleanup("QApplication", lambda: _delete_qt_object(owner._app))
    owner._engine = None
    owner._app = None
    _restore_qml_environment(previous_qml_environment)


def _shutdown_app_runtime(owner) -> None:
    """Release QML before QApplication teardown. 在 QApplication 析构前释放 QML。"""
    from ..core.shadow import reset_dwm_sync_filter
    from ..core.task_runner import TaskShutdownTimeoutError, shutdown_tasks

    report = shutdown_tasks(owner._task_shutdown_timeout_ms)
    if not report.complete:
        raise TaskShutdownTimeoutError(report)
    if owner._input_filter_started:
        _run_app_cleanup("input filter", reset_input_focus_filter)
        owner._input_filter_started = False
    if owner._dwm_filter_started:
        _run_app_cleanup("DWM filter", reset_dwm_sync_filter)
        owner._dwm_filter_started = False
    _run_app_cleanup("QML windows", _delete_remaining_qml_windows)
    _run_app_cleanup("current window", _clear_current_window_reference)
    owner._windows.clear()
    if owner._engine_publish_started:
        if EngineManager._engine is owner._engine:
            _run_app_cleanup("engine bindings", EngineManager.reset)
        owner._engine_publish_started = False
    _run_app_cleanup("QML engine", lambda: _delete_qt_object(owner._engine))
    owner._engine = None


class App(ApplicationIconMixin):
    """
    PrismQML应用入口 PrismQML Application Entry

    统一的应用管理类，封装QApplication常用API。

    Example:
        ```python
        from prismqml import App, Window

        app = App()
        window = app.create_window()
        window.show()
        app.exec()
        ```

    ``allow_qml_file_read`` 默认启用 Translator 读取本地 i18n JSON 所需的
    QML XHR；传入 ``False`` 可在创建引擎前显式关闭。
    ``task_shutdown_timeout_ms`` 可为后台任务退出设置总截止时间；超时会保留
    Qt 运行时并抛出 ``TaskShutdownTimeoutError``，传入 ``None`` 则安全地持续等待。
    """

    _instance: "App" = None

    def __init__(
        self,
        argv: List[str] = None,
        *,
        allow_qml_file_read: bool = True,
        task_shutdown_timeout_ms: Optional[int] = None,
        application_icon: Optional[Union[str, os.PathLike]] = None,
        application_icon_colored: bool = True,
    ):
        if App._instance is not None:
            raise RuntimeError(
                "App already exists. Use App.instance() to get the existing instance."
            )
        _initialize_app_state(self, task_shutdown_timeout_ms)
        previous_qml_environment = os.environ.get(
            QML_XHR_ALLOW_FILE_READ_ENV, _MISSING_ENVIRONMENT
        )
        committed = False
        try:
            _prepare_app_environment(allow_qml_file_read)
            _create_qt_application(self, argv or [])
            _create_qml_engine(self)
            configure_initial_application_icon(
                self, application_icon, application_icon_colored
            )
            App._instance = self
            committed = True
        finally:
            if not committed:
                _rollback_app_initialization(self, previous_qml_environment)

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
        from ..core.shadow import reset_dwm_sync_filter

        reset_input_focus_filter()
        reset_dwm_sync_filter()
        EngineManager.reset()
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

    def create_window(self, window_type: int = _DEFAULT_WINDOW_TYPE) -> "Window":
        """创建窗口 Create window

        Args:
            window_type: 窗口类型，使用 WindowType 枚举
                - WindowType.SPLIT (0): 展开式侧边导航
                - WindowType.BAR (1): 紧凑侧边导航（默认）
                - WindowType.FILLED (2): 填充式分割窗口

        Returns:
            Window 实例
        """
        from .fluent_window import Window

        window = Window(window_type=window_type)
        apply_application_icon_to_window(self, window)
        self._windows.append(window)
        return window

    def enable_auto_update(
        self,
        repo: str,
        current_version: str,
        asset_keyword: str = "Setup",
    ) -> "Updater":
        """Wire the engine-level auto-update backend. 启用引擎级自动更新底层。

        创建 ``Updater`` 并以 ``appUpdater`` 注入 QML 根上下文,供
        ``AutoUpdater { updater: appUpdater }`` 门面消费。应用侧仅需提供
        仓库与当前版本,即可复用检测→下载→启动安装程序的完整流程。与 C++
        ``App::enableAutoUpdate`` 对称。以最后一次调用为准重建底层实例,
        其生命周期由 App 持有。

        Args:
            repo: GitHub 仓库 "owner/repo"。
            current_version: 当前应用版本(如 "v1.0.3")。
            asset_keyword: 从 release assets 中挑安装包的关键词(默认 "Setup")。

        Returns:
            创建的 ``Updater`` 实例;引擎未就绪时返回 ``None``。
        """
        from ..core import Updater

        if self._engine is None:
            from ..core.logger import warning

            warning("App enable_auto_update: 引擎未就绪，无法启用自动更新")
            return None
        # 以最后一次调用为准重建底层 Updater;parent=None,生命周期由 self 持有。
        self._updater = Updater(repo, current_version, asset_keyword, None)
        self._updater.set_require_artifact_digest(True)
        self._engine.rootContext().setContextProperty("appUpdater", self._updater)
        return self._updater

    @property
    def engine(self) -> Optional[QQmlApplicationEngine]:
        """Get the live QML engine, or None after exec returns. 获取活动引擎，exec 返回后为 None。"""
        return self._engine

    @property
    def windows(self) -> List["WindowCore"]:
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

    def shutdown(self) -> None:
        """Safely release tasks and the QML runtime. 安全释放任务和 QML 运行时。"""
        _shutdown_app_runtime(self)

    def exec(self) -> int:
        """Run once, then release the QML runtime in dependency order. 运行一次并按依赖顺序释放 QML 运行时。"""
        try:
            return self._app.exec()
        finally:
            self.shutdown()

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
