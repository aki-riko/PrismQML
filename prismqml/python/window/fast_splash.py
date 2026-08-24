# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Fast independent startup splash for the Gallery entry point. Gallery 快速独立启动页。"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QMetaObject, QObject, QTimer, QUrl, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow

from ..core.logger import exception, info, warning
from ..runtime.fast_splash_context import register_fast_splash_context


# These values are the resolved Gallery splash metrics. They deliberately stay
# in this lightweight module so the fast surface does not import PrismQML/QML
# theme providers before the main engine is ready.
# 这些是 Gallery 启动画面的已解析度量，保留在轻量模块中，避免快速表面在主引擎
# 就绪前导入 PrismQML/QML 主题 provider。
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
_FADE_IN_DURATION = 150
_ICON_SHADOW_COLOR = "#30000000"
_ICON_SHADOW_BLUR = 0.8
_ICON_SHADOW_OFFSET = 6
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
    property bool contentVisible: false

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
        opacity: win.contentVisible ? 1 : 0

        Behavior on opacity {{
            NumberAnimation {{
                duration: {fade_in_duration}
                easing.type: Easing.OutCubic
            }}
        }}

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
        fade_in_duration=_FADE_IN_DURATION,
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
        self._splash_frame_count = 0
        self._main_frame_count = 0
        self._handoff_done = False
        self._embedded_handoff = False

    @property
    def splash(self) -> Optional[QQuickWindow]:
        return self._splash

    def show(self, icon: str = "") -> bool:
        """Create and show the splash before the main QML engine loads."""
        try:
            palette = self._app.palette()
            is_dark = palette.window().color().lightness() < 128
            self._splash_engine = QQmlEngine()
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
            if initial_icon:
                splash.setProperty("splashIcon", self._qml_icon_source(initial_icon))
            screen = self._app.primaryScreen()
            if screen is not None:
                available = screen.availableGeometry()
                splash.setPosition(
                    available.x() + (available.width() - splash.width()) // 2,
                    available.y() + (available.height() - splash.height()) // 2,
                )
            splash.frameSwapped.connect(self._on_splash_frame)
            splash.show()
            splash.setProperty("contentVisible", True)
            info("FastSplash 独立启动页已显示")
            return True
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as exc:
            exception(f"FastSplash 创建失败: {type(exc).__name__}: {exc}")
            return False

    @staticmethod
    def _qml_icon_source(icon: str) -> str:
        """Normalize a known icon source for the isolated QML engine."""
        source = str(icon).replace("\\", "/")
        if source.startswith(":/"):
            return "qrc" + source
        if source.startswith(("qrc:/", "file:/", "http://", "https://")):
            return source
        if len(source) > 1 and source[1] == ":":
            return QUrl.fromLocalFile(source).toString()
        if source.startswith("/"):
            return QUrl.fromLocalFile(source).toString()
        return source

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
        title = main_window.property("splashTitle") or main_window.property("windowTitle")
        subtitle = main_window.property("splashSubtitle")
        icon = main_window.property("splashIcon") or main_window.property("windowIcon")
        if title:
            self._splash.setProperty("splashTitle", str(title))
        if subtitle is not None:
            self._splash.setProperty("splashSubtitle", str(subtitle))
        if icon:
            self._splash.setProperty("splashIcon", str(icon))

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
        if self._handoff_done or self._splash is None or self._main_window is None:
            return
        self._handoff_done = True
        self._splash.setFlag(Qt.WindowType.WindowTransparentForInput, True)
        self._splash.setVisible(False)

        def activate_main() -> None:
            info("FastSplash 自定义 Splash 已绘制, 交接主窗口")
            self._main_window.raise_()
            self._main_window.requestActivate()

        QTimer.singleShot(0, activate_main)

    def _inject_context(self) -> None:
        register_fast_splash_context(self._splash_engine)

    def _finish_reveal(self) -> None:
        if self._handoff_done or self._splash is None or self._main_window is None:
            return
        splash = self._splash

        gate = {"hidden_frame": False, "closed": False}

        def handoff() -> None:
            if gate["closed"] or not gate["hidden_frame"]:
                return
            gate["closed"] = True
            self._handoff_done = True
            try:
                splash.frameSwapped.disconnect(on_hidden_frame)
            except (RuntimeError, TypeError):
                pass
            splash.setFlag(Qt.WindowType.WindowTransparentForInput, True)
            splash.setVisible(False)

            def activate_main() -> None:
                info("FastSplash 揭幕完成, 交接主窗口")
                self._main_window.raise_()
                self._main_window.requestActivate()

            QTimer.singleShot(0, activate_main)

        def on_hidden_frame() -> None:
            gate["hidden_frame"] = True
            handoff()

        splash.frameSwapped.connect(on_hidden_frame)
        splash.requestUpdate()

        def handoff_timeout() -> None:
            if gate["closed"]:
                return
            gate["hidden_frame"] = True
            handoff()

        QTimer.singleShot(250, handoff_timeout)

    @staticmethod
    def _bind_owner(splash: QQuickWindow, main: QQuickWindow) -> bool:
        splash.setTransientParent(main)
        if sys.platform != "win32":
            return splash.transientParent() == main
        splash_hwnd = int(splash.winId())
        main_hwnd = int(main.winId())
        if not splash_hwnd or not main_hwnd:
            return False
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        set_owner = user32.SetWindowLongPtrW
        set_owner.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
        set_owner.restype = ctypes.c_ssize_t
        ctypes.set_last_error(0)
        set_owner(splash_hwnd, -8, main_hwnd)
        if ctypes.get_last_error():
            return False
        get_owner = user32.GetWindow
        get_owner.argtypes = [wintypes.HWND, wintypes.UINT]
        get_owner.restype = wintypes.HWND
        return int(get_owner(splash_hwnd, 4) or 0) == main_hwnd

    @staticmethod
    def _raise_owned_splash(splash: QQuickWindow, main: QQuickWindow) -> None:
        if sys.platform != "win32":
            splash.raise_()
            return
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        set_window_pos = user32.SetWindowPos
        set_window_pos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        set_window_pos.restype = wintypes.BOOL
        flags = 0x0001 | 0x0002 | 0x0010  # SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
        # HWND_TOP is normal Z-order, not a system topmost window. The native
        # owner set by _bind_owner keeps this window attached to the main window.
        # HWND_TOP 是普通 Z 序, 不是系统置顶窗口; owner 关系负责绑定生命周期。
        set_window_pos(int(splash.winId()), wintypes.HWND(0), 0, 0, 0, 0, flags)

    def close(self) -> None:
        """Hide the retained QQuickWindow during application teardown."""
        if self._ready_timer is not None:
            self._ready_timer.stop()
        if self._splash is not None:
            try:
                self._splash.setVisible(False)
            except RuntimeError:
                pass
