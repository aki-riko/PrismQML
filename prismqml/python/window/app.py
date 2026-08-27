# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
PrismQML 应用入口类 PrismQML Application Entry

提供统一的应用管理API，封装 QApplication 常用操作。
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, List, Optional, Union

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication, QIcon

from ..core.utils import QML_XHR_ALLOW_FILE_READ_ENV
from ._application_icon_runtime import (
    ApplicationIconMixin,
    apply_application_icon_to_window,
    configure_initial_application_icon,
    initialize_application_icon_state,
)

if TYPE_CHECKING:
    from PySide6.QtQml import QQmlApplicationEngine

    from .fluent_window import Window
    from .window_core import WindowCore

_DEFAULT_WINDOW_TYPE = 1
_MISSING_ENVIRONMENT = object()
_QML_ENGINE_DELETE_TIMEOUT_MS = 1000


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
    owner._fast_splash = None
    owner._startup_window_registrar = None
    initialize_application_icon_state(owner)


def _prepare_app_environment(allow_qml_file_read: bool, config_path) -> None:
    """Prepare process-wide Qt settings. 准备进程级 Qt 设置。"""
    from ..runtime import prepare_application_environment

    prepare_application_environment(allow_qml_file_read, config_path)


def _create_qt_application(
    owner,
    argv: List[str],
    application_icon=None,
    splash_subtitle: Optional[str] = None,
    splash_width: Optional[int] = None,
    splash_height: Optional[int] = None,
) -> None:
    """Create QApplication and install global filters. 创建应用并安装全局过滤器。"""
    from ..runtime import (
        create_qt_application,
        install_application_dwm_filter,
        install_application_input_filter,
    )

    owner._app, owner._owns_app = create_qt_application(argv)
    owner._input_filter_started = True
    install_application_input_filter(owner._app)
    from .fast_splash import FastSplashController

    owner._fast_splash = FastSplashController(owner._app)
    owner._fast_splash.show(
        application_icon or "",
        subtitle=splash_subtitle,
        splash_width=splash_width,
        splash_height=splash_height,
    )
    install_application_dwm_filter()
    owner._dwm_filter_started = True


def _create_qml_engine(owner, config_path, persist_appearance) -> None:
    """Create and fully register the QML engine. 创建并完整注册 QML 引擎。"""
    from ..runtime import (
        configure_application_engine,
        create_qml_engine,
        publish_qml_engine,
        register_startup_window_context,
    )

    owner._engine = create_qml_engine()
    owner._engine_publish_started = True
    publish_qml_engine(owner._engine)
    configure_application_engine(
        owner._engine,
        config_path=config_path,
        persist_appearance=persist_appearance,
    )
    owner._startup_window_registrar = register_startup_window_context(
        owner._engine, owner
    )


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


def _delete_qml_engine(value) -> None:
    """Delete a QML engine from a live Qt event loop. 在活动 Qt 事件循环中销毁 QML 引擎。"""
    import shiboken6

    if value is None or not shiboken6.isValid(value):
        return
    loop = QEventLoop()
    timeout_timer = QTimer()
    timeout_timer.setSingleShot(True)
    timeout_timer.timeout.connect(loop.quit)
    value.destroyed.connect(loop.quit)
    QTimer.singleShot(0, value.deleteLater)
    timeout_timer.start(_QML_ENGINE_DELETE_TIMEOUT_MS)
    loop.exec()
    timeout_timer.stop()
    if shiboken6.isValid(value):
        raise RuntimeError("QML engine deferred deletion timed out")


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
    from ..runtime import (
        is_published_qml_engine,
        reset_application_dwm_filter,
        reset_application_input_filter,
        reset_qml_engine,
    )

    if owner._fast_splash is not None:
        _run_app_cleanup("fast splash", owner._fast_splash.close)
        owner._fast_splash = None
    if owner._input_filter_started:
        _run_app_cleanup("input filter", reset_application_input_filter)
    if owner._engine_publish_started and is_published_qml_engine(owner._engine):
        _run_app_cleanup("engine bindings", reset_qml_engine)
    if owner._dwm_filter_started:
        _run_app_cleanup("DWM filter", reset_application_dwm_filter)
    _run_app_cleanup("QML engine", lambda: _delete_qml_engine(owner._engine))
    if owner._owns_app:
        _run_app_cleanup("QApplication", lambda: _delete_qt_object(owner._app))
    owner._engine = None
    owner._app = None
    _restore_qml_environment(previous_qml_environment)


def _shutdown_app_runtime(owner) -> None:
    """Release QML before QApplication teardown. 在 QApplication 析构前释放 QML。"""
    from ..core.task_runner import TaskShutdownTimeoutError, shutdown_tasks
    from ..runtime import (
        get_config_manager,
        is_published_qml_engine,
        release_qml_engine_bindings,
        reset_application_dwm_filter,
        reset_application_input_filter,
        reset_qml_engine,
    )

    if owner._fast_splash is not None:
        _run_app_cleanup("fast splash", owner._fast_splash.close)
        owner._fast_splash = None
    config_manager = get_config_manager()
    if not config_manager.waitForPersistence(owner._task_shutdown_timeout_ms):
        raise RuntimeError("配置持久化在应用关闭前未完成")
    report = shutdown_tasks(owner._task_shutdown_timeout_ms)
    if not report.complete:
        raise TaskShutdownTimeoutError(report)
    if owner._input_filter_started:
        _run_app_cleanup("input filter", reset_application_input_filter)
        owner._input_filter_started = False
    if owner._dwm_filter_started:
        _run_app_cleanup("DWM filter", reset_application_dwm_filter)
        owner._dwm_filter_started = False
    if owner._engine_publish_started and is_published_qml_engine(owner._engine):
        _run_app_cleanup(
            "engine surfaces",
            lambda: release_qml_engine_bindings(
                owner._engine, include_lazy=False
            ),
        )
    _run_app_cleanup("QML windows", _delete_remaining_qml_windows)
    _run_app_cleanup("current window", _clear_current_window_reference)
    owner._windows.clear()
    if owner._engine_publish_started:
        if is_published_qml_engine(owner._engine):
            _run_app_cleanup("engine bindings", reset_qml_engine)
        owner._engine_publish_started = False
    _run_app_cleanup("QML engine", lambda: _delete_qml_engine(owner._engine))
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
    ``auto_update_slot_redirect`` 默认读取安装器双槽状态并在创建 Qt 前切换到
    下次启动槽；源码开发态和普通单目录安装不受影响。
    ``config_path`` 可指定应用独立配置；显式路径默认启用外观持久化。
    ``persist_appearance=False`` 可让宿主自行管理主题、皮肤、语言和主题色。
    ``splash_subtitle`` 可在快速启动页首帧显示自定义副标题。
    ``splash_width`` / ``splash_height`` 可指定快速启动页初始尺寸；绑定窗口后
    引擎仍会以主窗口实际逻辑尺寸为准。
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
        splash_subtitle: Optional[str] = None,
        splash_width: Optional[int] = None,
        splash_height: Optional[int] = None,
        auto_update_slot_redirect: bool = True,
        config_path: Optional[Union[str, os.PathLike]] = None,
        persist_appearance: Optional[bool] = None,
    ):
        if App._instance is not None:
            raise RuntimeError(
                "App already exists. Use App.instance() to get the existing instance."
            )
        if auto_update_slot_redirect:
            from ..core.update_slots import redirect_to_active_update_slot

            forwarded_args = None if argv is None else list(argv[1:])
            if redirect_to_active_update_slot(forwarded_args):
                raise SystemExit(0)
        _initialize_app_state(self, task_shutdown_timeout_ms)
        previous_qml_environment = os.environ.get(
            QML_XHR_ALLOW_FILE_READ_ENV, _MISSING_ENVIRONMENT
        )
        committed = False
        try:
            _prepare_app_environment(allow_qml_file_read, config_path)
            _create_qt_application(
                self,
                argv or [],
                application_icon,
                splash_subtitle,
                splash_width,
                splash_height,
            )
            _create_qml_engine(self, config_path, persist_appearance)
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
        from ..runtime import (
            reset_application_dwm_filter,
            reset_application_input_filter,
            reset_qml_engine,
        )

        if cls._instance is not None and cls._instance._fast_splash is not None:
            cls._instance._fast_splash.close()
            cls._instance._fast_splash = None
        reset_application_input_filter()
        reset_application_dwm_filter()
        reset_qml_engine()
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
        cls._update_fast_splash_metadata(title=name)

    @classmethod
    def setApplicationDisplayName(cls, name: str) -> None:
        """设置应用显示名称并同步启动页 Set display name and sync startup splash"""
        QApplication.setApplicationDisplayName(name)
        cls._update_fast_splash_metadata(title=name)

    @classmethod
    def _update_fast_splash_metadata(cls, **metadata) -> None:
        """Forward application branding to the engine-owned splash."""
        instance = cls._instance
        if instance is None:
            return
        controller = getattr(instance, "_fast_splash", None)
        if controller is not None:
            controller.update_metadata(**metadata)

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

    def setWindowIcon(self, icon) -> None:
        """设置应用图标并同步可识别的启动页来源 Set app icon and sync splash source."""
        self._app.setWindowIcon(icon)
        if isinstance(icon, (str, os.PathLike)):
            self._update_fast_splash_metadata(icon=os.fspath(icon))
        elif isinstance(icon, QIcon):
            # Preserve the legacy QIcon overload for the early isolated splash.
            # 兼容旧版 QIcon 重载，让早期独立 Splash 也能拿到同一份图标。
            self._update_fast_splash_metadata(icon=icon)

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
        *,
        install_strategy: str = "in_place",
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
            install_strategy: ``in_place`` 或 Windows ``dual_slot``。

        Returns:
            创建的 ``Updater`` 实例;引擎未就绪时返回 ``None``。
        """
        from ..runtime import enable_auto_update

        return enable_auto_update(
            self,
            repo,
            current_version,
            asset_keyword,
            install_strategy=install_strategy,
        )

    @property
    def engine(self) -> Optional[QQmlApplicationEngine]:
        """Get the live QML engine, or None after exec returns. 获取活动引擎，exec 返回后为 None。"""
        return self._engine

    @property
    def windows(self) -> List["WindowCore"]:
        """获取所有窗口 Get all windows"""
        return self._windows

    def attach_startup_window(self, main_window) -> bool:
        """Attach a QML-created window to the engine-owned startup surface."""
        controller = self._fast_splash
        if controller is None or self._engine is None or main_window is None:
            return False
        attached_window = getattr(controller, "_main_window", None)
        if attached_window is not None:
            return attached_window is main_window
        return controller.attach_to_window(self._engine, main_window)

    def _attach_fast_splash(self, main_window) -> bool:
        """Compatibility wrapper for the former private attach hook."""
        return self.attach_startup_window(main_window)

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
    # classmethod / property / setWindowIcon 不会被遮蔽.
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
