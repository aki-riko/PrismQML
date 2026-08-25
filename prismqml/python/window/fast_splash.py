# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Fast independent startup splash for the Gallery entry point. Gallery 快速独立启动页。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QMetaObject, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow

from ..core.logger import exception, info, warning
from ..runtime.fast_splash_context import register_fast_splash_context
from ._fast_splash_metadata import (
    ICON_PROVIDER_NAME,
    FastSplashIconProvider,
    application_title,
    is_default_process_title,
    qml_icon_source,
    set_icon_metadata,
)
from ._fast_splash_lifecycle import (
    bind_owner,
    close as close_fast_splash,
    finish_embedded_handoff,
    finish_reveal,
    raise_owned_splash,
)


# Resolved metrics stay local so the fast surface avoids early theme imports.
# 已解析度量保留在本模块，避免快速表面过早导入主题 provider。
_ICON_SIZE = 102
_SPACING_XL = 16
_SPACING_M = 8
_TITLE_PX = 20
_TITLE_WEIGHT = 600
_TITLE_FAMILY = "Microsoft YaHei UI"
_BODY_PX = 14
_RING_SIZE = 20
_RING_STROKE = 2.0
_DOT_SIZE = 6
_DOT_RADIUS = 2
_DOT_TOP = -1
_TRACK_OPACITY = 0.3
_SPIN_DURATION = 1000
_BREATHE_MIN = 0.9
_BREATHE_MAX = 1.1
_BREATHE_DURATION = 1200
_ICON_SHADOW_COLOR = "#30000000"
_ICON_SHADOW_BLUR = 0.8
_BACKGROUND_DARK = "#202020"
_BACKGROUND_LIGHT = "#f0f4f9"
_ACCENT = "#ff0e5a9c"


_SPLASH_QML = """
import QtQuick
import QtQuick.Effects

Window {{
    id: win
    width: 1200; height: 800
    flags: Qt.SplashScreen | Qt.FramelessWindowHint
    color: "transparent"
    // The controller shows the window after the object tree and metadata are ready.
    // 由控制器在对象树和元数据准备完成后显示窗口，避免构造期间提交空白帧。
    visible: false

    property string splashIcon: ""
    property string splashTitle: "PrismQML"
    property string splashSubtitle: "正在加载组件..."

    property Item revealRoot: revealSurface
    readonly property string layerState:
        "enabled=" + revealSurface.layer.enabled
        + " effect=" + (revealSurface.layer.effect ? "set" : "null")
        + " smooth=" + revealSurface.layer.smooth
    property var revealTransition: null
    readonly property bool revealRingActive:
        revealTransition ? revealTransition.active : false

    Item {{
        id: revealSurface
        anchors.fill: parent
        property bool spinnerVisible: true

        Rectangle {{
            anchors.fill: parent
            radius: 8
            color: "{background}"
        }}

        Column {{
            anchors.centerIn: parent
            spacing: 16

            Item {{
                id: iconContainer
                anchors.horizontalCenter: parent.horizontalCenter
                width: 102; height: 102
                layer.enabled: true
                layer.effect: MultiEffect {{
                    shadowEnabled: true
                    shadowColor: "#30000000"
                    shadowBlur: 0.8
                    shadowVerticalOffset: 6
                }}

                Image {{
                    anchors.centerIn: parent
                    width: 102; height: 102
                    source: win.splashIcon
                    sourceSize.width: 102
                    sourceSize.height: 102
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                    asynchronous: false
                    visible: source !== ""
                }}

                SequentialAnimation {{
                    running: true
                    loops: Animation.Infinite
                    NumberAnimation {{
                        target: iconContainer; property: "scale"
                        to: 1.1; duration: 1200
                        easing.type: Easing.InOutQuad
                    }}
                    NumberAnimation {{
                        target: iconContainer; property: "scale"
                        to: 0.9; duration: 1200
                        easing.type: Easing.InOutQuad
                    }}
                }}
            }}

            Text {{
                anchors.horizontalCenter: parent.horizontalCenter
                text: win.splashTitle
                color: "{title_color}"
                font.family: "Microsoft YaHei UI"
                font.pixelSize: 20
                font.weight: 600
            }}

            Row {{
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 8

                Item {{
                    width: 20; height: 20
                    anchors.verticalCenter: parent.verticalCenter

                    Rectangle {{
                        anchors.fill: parent
                        radius: width / 2
                        color: "transparent"
                        border.width: 2
                        border.color: "#ff0e5a9c"
                        opacity: 0.3
                    }}

                    Item {{
                        id: spinner
                        anchors.fill: parent
                        visible: revealSurface.spinnerVisible

                        Rectangle {{
                            width: 6; height: 6
                            radius: 2
                            color: "#ff0e5a9c"
                            x: parent.width / 2 - width / 2
                            y: -1
                        }}

                        // Render-thread animation keeps moving while the main
                        // QML engine creates its page tree.
                        // 渲染线程动画确保主 QML 引擎创建页面树时小圈仍在转动。
                        RotationAnimator on rotation {{
                            running: true
                            loops: Animation.Infinite
                            from: 0; to: 360; duration: 1000
                        }}
                    }}
                }}

                Text {{
                    anchors.verticalCenter: parent.verticalCenter
                    text: win.splashSubtitle
                    color: "{body_color}"
                    font.family: "Microsoft YaHei UI"
                    font.pixelSize: 14
                }}
            }}
        }}
    }}

    Rectangle {{
        id: revealRing
        property real radiusPx: win.revealTransition
            ? win.revealTransition.revealRadiusPixels : 8
        x: parent.width * 0.5 - radiusPx
        y: parent.height * 0.5 - radiusPx
        width: radiusPx * 2
        height: radiusPx * 2
        radius: width * 0.5
        color: "transparent"
        border.width: 2
        border.color: "#ff0e5a9c"
        opacity: 0.72
        visible: win.revealRingActive
        z: 100
    }}
}}
"""

_REVEAL_QML = """
import QtQuick
import "{root_url}"
import "{internal_url}" as NavigationInternal

NavigationInternal.LazyPageCircleTransition {{
    id: transition
    objectName: "fastStartupReveal"
    anchors.fill: parent
    revealTarget: true
    revealDuration: 400
    revealEasing: Easing.Linear
    keepSourceHiddenOnExpand: true
    property Item revealTargetItem: null
    signal revealDone()

    onExpandFinished: {{
        transition.revealDone()
    }}

    function go() {{ return transition.expand(transition.revealTargetItem) }}
}}
"""


def build_fast_splash_qml(is_dark: bool) -> str:
    """Build the lightweight splash surface without importing PrismQML."""
    return _SPLASH_QML.format(
        background=_BACKGROUND_DARK if is_dark else _BACKGROUND_LIGHT,
        title_color="#ffffffff" if is_dark else "#ff000000",
        body_color="#99ffffff" if is_dark else "#99000000",
    )


class FastSplashController(QObject):
    """Own the independent splash and its single-window reveal handoff."""

    def __init__(self, app: QObject, main_engine: Optional[QQmlEngine] = None):
        super().__init__(app)
        self._app = app
        self._main_engine = main_engine
        self._splash_engine: Optional[QQmlEngine] = None
        self._splash_component: Optional[QQmlComponent] = None
        self._reveal_component: Optional[QQmlComponent] = None
        self._splash: Optional[QQuickWindow] = None
        self._transition = None
        self._main_window: Optional[QQuickWindow] = None
        self._ready_timer: Optional[QTimer] = None
        self._icon_provider: Optional[FastSplashIconProvider] = None
        self._splash_frame_count = 0
        self._main_frame_count = 0
        self._page_ready_observed_frame = -1
        self._handoff_done = False
        self._embedded_handoff = False
        self._visibility_deferred = False
        self._title_metadata_ready = False
        self._icon_metadata_ready = False
        self._closed = False

    @property
    def splash(self) -> Optional[QQuickWindow]:
        return self._splash

    def show(self, icon: str = "", *, subtitle: Optional[str] = None) -> bool:
        """Create the splash before QML loads, deferring unbranded frames."""
        try:
            self._closed = False
            self._handoff_done = False
            self._embedded_handoff = False
            self._main_window = None
            self._transition = None
            self._ready_timer = None
            self._page_ready_observed_frame = -1
            self._splash_frame_count = 0
            self._main_frame_count = 0
            self._title_metadata_ready = False
            self._icon_metadata_ready = False
            palette = self._app.palette()
            is_dark = palette.window().color().lightness() < 128
            self._splash_engine = QQmlEngine()
            self._icon_provider = FastSplashIconProvider()
            self._splash_engine.addImageProvider(ICON_PROVIDER_NAME, self._icon_provider)
            self._splash_component = QQmlComponent(self._splash_engine)
            self._splash_component.setData(
                build_fast_splash_qml(is_dark).encode("utf-8"),
                QUrl("fast-startup-splash"),
            )
            if self._splash_component.isError():
                warning(
                    "FastSplash QML 创建失败: "
                    + "; ".join(error.toString() for error in self._splash_component.errors())
                )
                return False
            splash = self._splash_component.create()
            if not isinstance(splash, QQuickWindow):
                warning("FastSplash QML 根对象不是 QQuickWindow")
                return False
            self._splash = splash
            initial_icon = icon or getattr(self._app, "application_icon", "")
            initial_icon_ready = False
            if initial_icon:
                initial_icon_ready = self._set_icon_metadata(initial_icon)
            application_title = self._application_title(self._app)
            self._title_metadata_ready = bool(
                application_title and not self._is_default_process_title(application_title)
            )
            self._icon_metadata_ready = initial_icon_ready
            # Constructor-level branding is complete when both static title and
            # icon were supplied. Window.showSplash() still updates the same
            # surface later for legacy callers that provide metadata at window
            # construction time.
            # App 构造器同时提供静态标题和图标时元数据已完整；旧调用方仍可在
            # Window.showSplash() 时补交窗口级元数据并更新同一启动页。
            if subtitle is not None:
                splash.setProperty("splashSubtitle", str(subtitle))
            self._visibility_deferred = not (
                self._title_metadata_ready and self._icon_metadata_ready
            )
            if application_title and not self._is_default_process_title(application_title):
                splash.setProperty("splashTitle", str(application_title))
            screen = self._app.primaryScreen()
            if screen is not None:
                available = screen.availableGeometry()
                splash.setPosition(
                    available.x() + (available.width() - splash.width()) // 2,
                    available.y() + (available.height() - splash.height()) // 2,
                )
            splash.frameSwapped.connect(self._on_splash_frame)
            if self._visibility_deferred:
                info("FastSplash 已创建，等待应用窗口元数据后显示")
            else:
                splash.show()
                info("FastSplash 独立启动页已显示")
            return True
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as exc:
            exception(f"FastSplash 创建失败: {type(exc).__name__}: {exc}")
            return False

    _application_title = staticmethod(application_title)
    _is_default_process_title = staticmethod(is_default_process_title)

    def update_metadata(
        self,
        *,
        title: Optional[str] = None,
        icon: Any = None,
        subtitle: Optional[str] = None,
    ) -> None:
        """Update visible startup metadata without changing its public API."""
        if self._closed or self._splash is None:
            return
        try:
            if title:
                self._splash.setProperty("splashTitle", str(title))
                self._title_metadata_ready = not self._is_default_process_title(title)
            if icon:
                self._icon_metadata_ready = self._set_icon_metadata(icon)
            if subtitle is not None:
                self._splash.setProperty("splashSubtitle", str(subtitle))
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            warning(f"FastSplash 元数据更新失败: {type(exc).__name__}: {exc}")

    def mark_window_metadata_ready(self) -> None:
        """Release the early surface after Window splash configuration is complete."""
        if self._closed or self._splash is None:
            return
        self._show_deferred_splash()

    def show_if_metadata_ready(self) -> None:
        """Show after a complete pre-window branding transaction.

        Python-managed windows publish their final title, icon, and subtitle
        before creating the QML root.  Showing at that boundary removes the
        otherwise invisible construction gap while keeping the generic
        fallback hidden until the normal attach path can resolve its metadata.
        """
        if self._closed or self._splash is None:
            return
        if not (self._title_metadata_ready and self._icon_metadata_ready):
            return
        self._show_deferred_splash()

    def _set_icon_metadata(self, icon: Any) -> bool:
        """Publish a path/URL or legacy QIcon to the isolated QML surface."""
        return set_icon_metadata(self._splash, self._icon_provider, icon)

    def _show_deferred_splash(self) -> None:
        """Show a deferred splash after the real window metadata is ready."""
        if (
            self._closed
            or self._handoff_done
            or not self._visibility_deferred
            or self._splash is None
        ):
            return
        self._splash.show()
        self._visibility_deferred = False
        info("FastSplash 独立启动页已显示")

    _qml_icon_source = staticmethod(qml_icon_source)

    def attach_and_reveal(self, main_engine: QQmlEngine, main_window: QQuickWindow) -> bool:
        """Bind the splash to the main HWND and reveal once its first page paints."""
        self._main_engine = main_engine
        self._main_window = main_window
        if self._splash is None:
            return False
        try:
            info(
                "FastSplash 绑定主窗口: "
                f"hwnd={int(main_window.winId())}, "
                f"stack={main_window.property('stackedWidget') is not None}"
            )
            if not self._bind_owner(self._splash, main_window):
                warning("FastSplash 原生 owner 绑定校验失败")
                return False
            self._show_deferred_splash()
            self._show_qml_owned_window(main_window)
            self._raise_owned_splash(self._splash, main_window)
            main_window.frameSwapped.connect(self._on_main_frame)
            self._ready_timer = QTimer(self)
            self._ready_timer.setInterval(8)
            self._ready_timer.timeout.connect(self._poll_main_ready)
            self._ready_timer.start()
            return True
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as exc:
            exception(f"FastSplash 绑定主窗口失败: {type(exc).__name__}: {exc}")
            return False

    def attach_to_window(
        self, main_engine: QQmlEngine, main_window: QQuickWindow
    ) -> bool:
        """Route one window through the fast or embedded splash lifecycle."""
        try:
            self._sync_window_metadata(main_window)
            uses_default = main_window.property("_usesDefaultSplashComponent")
            if uses_default is True:
                # The root is still hidden here, so disabling the loader does not
                # create a visible gap before the independent surface is bound.
                main_window.setProperty("splashEnabled", False)
                if self.attach_and_reveal(main_engine, main_window):
                    return True
                return self.restore_embedded_splash(main_window)
            if uses_default is False:
                return self.handoff_to_embedded(main_engine, main_window)
            warning("FastSplash 无法识别 Splash 组件，回退内嵌生命周期")
            return self.restore_embedded_splash(main_window)
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            exception(f"FastSplash 启动分流失败: {type(exc).__name__}: {exc}")
            return self.restore_embedded_splash(main_window)

    def _sync_window_metadata(self, main_window: QQuickWindow) -> None:
        """Copy existing window splash metadata into the early surface."""
        if self._splash is None:
            return
        title = (
            main_window.property("splashTitle")
            or main_window.property("windowTitle")
            or self._application_title(self._app)
        )
        subtitle = main_window.property("splashSubtitle")
        icon = (
            main_window.property("splashIcon")
            or main_window.property("windowIcon")
            or getattr(self._app, "application_icon", "")
        )
        self.update_metadata(title=title, icon=icon, subtitle=subtitle)
        self.mark_window_metadata_ready()

    def restore_embedded_splash(self, main_window: Optional[QQuickWindow] = None) -> bool:
        """Restore the normal QML splash after a fast-path failure or bypass."""
        target = main_window or self._main_window
        restored = False
        if target is not None:
            try:
                restored = bool(QMetaObject.invokeMethod(target, "_enableDeferredSplash"))
                if not restored:
                    warning("FastSplash 内嵌回退函数不可用，直接恢复 Splash Loader")
                    target.setProperty("splashEnabled", True)
                    restored = True
            except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                exception(f"FastSplash 内嵌回退失败: {type(exc).__name__}: {exc}")
        self.close()
        return restored

    def handoff_to_embedded(
        self, main_engine: QQmlEngine, main_window: QQuickWindow
    ) -> bool:
        """Keep the fast surface until a custom embedded splash is painted."""
        self._main_engine = main_engine
        self._main_window = main_window
        if self._splash is None:
            return self.restore_embedded_splash(main_window)
        try:
            if not self._bind_owner(self._splash, main_window):
                warning("FastSplash 自定义回退无法绑定主窗口")
                return self.restore_embedded_splash(main_window)
            self._show_deferred_splash()
            if not QMetaObject.invokeMethod(main_window, "_enableDeferredSplash"):
                warning("FastSplash 自定义回退无法启用内嵌 Splash")
                return self.restore_embedded_splash(main_window)
            self._show_qml_owned_window(main_window)
            self._raise_owned_splash(self._splash, main_window)
            self._embedded_handoff = True
            main_window.frameSwapped.connect(self._on_main_frame)
            self._ready_timer = QTimer(self)
            self._ready_timer.setInterval(8)
            self._ready_timer.timeout.connect(self._poll_main_ready)
            self._ready_timer.start()
            return True
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as exc:
            exception(f"FastSplash 自定义回退失败: {type(exc).__name__}: {exc}")
            return self.restore_embedded_splash(main_window)

    def _on_splash_frame(self) -> None:
        self._splash_frame_count += 1

    def _on_main_frame(self) -> None:
        self._main_frame_count += 1

    @staticmethod
    def _page_ready(main_window: QQuickWindow) -> bool:
        stack = main_window.property("stackedWidget")
        if stack is None:
            return False
        current = stack.property("currentWidget")
        if current is None:
            return False
        # Python-managed windows create page containers before their real page
        # content.  The container must not count as a loaded first page.
        # Python 页面由宿主先创建容器、后挂载内容，不能把容器误判为首屏就绪。
        if main_window.property("_pythonPageMode") is True:
            current_index = stack.property("currentIndex")
            ready_indexes = main_window.property("_pythonReadyIndexes")
            # PySide6 exposes QML `property var` values as QJSValue. Convert it
            # before applying the Python collection guard. PySide6 会把 QML
            # `property var` 暴露为 QJSValue，先转换再进行 Python 集合校验。
            to_variant = getattr(ready_indexes, "toVariant", None)
            if callable(to_variant):
                ready_indexes = to_variant()
            if not isinstance(current_index, int) or not isinstance(
                ready_indexes, (list, tuple)
            ):
                return False
            if current_index not in ready_indexes:
                return False
        if bool(stack.property("_useSourceMode")):
            return current.property("item") is not None
        return True

    @staticmethod
    def _show_qml_owned_window(main_window: QQuickWindow) -> None:
        """Expose a hidden pure-QML window after the splash owns its startup."""
        if main_window.property("_pythonPageMode") is True:
            return
        if not main_window.isVisible():
            main_window.show()

    def _poll_main_ready(self) -> None:
        if self._handoff_done or self._main_window is None:
            return
        if self._embedded_handoff:
            if self._main_frame_count < 1:
                return
            if self._main_window.property("_splashInstance") is None:
                return
            if self._main_window.property("_startupPresentationReady") is False:
                return
            if self._ready_timer is not None:
                self._ready_timer.stop()
            self._finish_embedded_handoff()
            return
        if self._main_frame_count < 3 or not self._page_ready(self._main_window):
            self._page_ready_observed_frame = -1
            return
        # A ready signal means the page tree is constructed, not that it has
        # reached the window surface. Require one frame after readiness so the
        # reveal never exposes a partially painted first page.
        # 页面就绪信号只代表页面树构建完成；必须再提交一帧后才能揭幕。
        if self._page_ready_observed_frame < 0:
            self._page_ready_observed_frame = self._main_frame_count
            return
        if self._main_frame_count <= self._page_ready_observed_frame:
            return
        if self._ready_timer is not None:
            self._ready_timer.stop()
        info(
            "FastSplash 主窗口就绪: "
            f"frames={self._main_frame_count}, splash_frames={self._splash_frame_count}"
        )
        # Re-raise inside the normal owner group after the main window's first
        # frames have entered the Windows Z-order. 揭幕前在普通 owner 窗口组内
        # 重新提升一次, 避免主窗口首帧提交后把 Splash 排到后面。
        self._raise_owned_splash(self._splash, self._main_window)
        self._start_reveal()

    def _start_reveal(self) -> None:
        if self._splash is None or self._main_engine is None or self._splash_engine is None:
            self.restore_embedded_splash()
            return
        try:
            for path in self._main_engine.importPathList():
                self._splash_engine.addImportPath(path)
            self._inject_context()
            lib_root = Path(__file__).resolve().parents[2] / "PrismQML"
            root_url = QUrl.fromLocalFile(str(lib_root)).toString()
            internal_url = QUrl.fromLocalFile(
                str(lib_root / "controls" / "navigation" / "_internal")
            ).toString()
            component = QQmlComponent(self._splash_engine)
            component.setData(
                _REVEAL_QML.format(root_url=root_url, internal_url=internal_url).encode("utf-8"),
                QUrl("fast-startup-reveal"),
            )
            # Keep the QQmlComponent alive with the controller. A component-created
            # object can still be destroyed when its temporary component wrapper
            # goes out of scope, even after assigning QObject ownership and a
            # visual parent. 将动态组件本身绑定到控制器生命周期；即使已经设置
            # QObject 所有权和 visual parent，临时 QQmlComponent wrapper 离开
            # 作用域仍可能回收它创建的揭幕对象。
            self._reveal_component = component
            transition = component.create()
            if transition is None:
                warning(
                    "FastSplash 揭幕组件创建失败: "
                    + "; ".join(error.toString() for error in component.errors())
                )
                self.restore_embedded_splash()
                return
            self._transition = transition
            root_item = self._splash.property("revealRoot")
            transition.setParentItem(root_item)
            # Keep QObject ownership on the controller; the item parent only
            # controls visual placement. 将 QObject 所有权交给控制器；item
            # 父级只负责视觉挂载，避免 QML 引擎提前回收揭幕对象。
            transition.setParent(self)
            QQmlEngine.setObjectOwnership(
                transition, QQmlEngine.ObjectOwnership.CppOwnership
            )
            transition.setProperty("revealTargetItem", root_item)
            self._splash.setProperty("revealTransition", transition)
            transition.revealDone.connect(self._finish_reveal)
            info("FastSplash 开始 400ms 线性圆环揭幕")
            if not QMetaObject.invokeMethod(transition, "go"):
                warning("FastSplash 揭幕启动失败")
                self.restore_embedded_splash()
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as exc:
            exception(f"FastSplash 揭幕失败: {type(exc).__name__}: {exc}")
            self.restore_embedded_splash()

    def _finish_embedded_handoff(self) -> None:
        finish_embedded_handoff(self)

    def _inject_context(self) -> None:
        register_fast_splash_context(self._splash_engine)

    def _finish_reveal(self) -> None:
        finish_reveal(self)

    def close(self) -> None:
        close_fast_splash(self)

    _bind_owner = staticmethod(bind_owner)
    _raise_owned_splash = staticmethod(raise_owned_splash)
