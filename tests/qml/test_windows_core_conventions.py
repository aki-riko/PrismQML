# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowsCore geometry and lifecycle contracts. 窗口核心几何与生命周期合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEasingCurve,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
    Slot,
)
from PySide6.QtGui import QGuiApplication, QWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

import prismqml.python.runtime.window_services as window_services_module
from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "prismqml" / "PrismQML" / "WindowsCore.qml"
# Enums.windowShadow.mode_qml, kept in sync with PrismEnums/WindowShadow.qml.
# 与 PrismEnums/WindowShadow.qml 保持同步。
_WINDOW_SHADOW_MODE_QML = 2
WINDOW_FRAME_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowsCoreFrame.qml"
)
RESIZE_HANDLES_TIMER_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "_internal"
    / "WindowsResizeHandlesTimer.qml"
)
WINDOW_ICON_DEFERRED_TIMER_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "_internal"
    / "WindowIconDeferredLoadTimer.qml"
)
ANIMATION_HELPER_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowAnimationHelper.qml"
)
WINDOW_CLOSE_FRAME_WAITER_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowCloseFrameWaiter.qml"
)
WINDOW_DRAG_HANDLE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "utils"
    / "WindowDragHandle.qml"
)
WINDOW_LEAF_PATHS = [
    ROOT / "prismqml" / "PrismQML" / "_internal" / name
    for name in (
        "QmlShadowHost.qml",
        "ResizeArea.qml",
        "WindowIcon.qml",
        "CaptionButton.qml",
        "ContentFrame.qml",
        "WindowsCoreFrame.qml",
    )
]
STARTUP_DIAGNOSTIC_PATHS = [
    ROOT / "prismqml" / "PrismQML" / "NavigationWindowCore.qml",
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowsBar.qml",
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowsBarContent.qml",
    ANIMATION_HELPER_PATH,
    *WINDOW_LEAF_PATHS,
]
WINDOW_BUILDER_PATH = (
    ROOT / "prismqml" / "python" / "window" / "_window_builder.py"
)
METRICS_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
ENUMS_PATH = ROOT / "prismqml" / "PrismQML" / "Enums.qml"
CAPTION_BUTTON_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "CaptionButton.qml"
)
REMOVED_CLOSE_EFFECT_PATHS = [
    ROOT / "prismqml" / "PrismQML" / relative_path
    for relative_path in (
        "_internal/WindowCloseDissolve.qml",
        "_internal/CloseRippleAnimator.qml",
        "_internal/CloseRippleDissolve.qml",
        "_internal/CloseRippleFrame.qml",
        "shaders/window_close_ripple.frag",
        "shaders/window_close_ripple.frag.qsb",
    )
]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "windows-core-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

WindowsCore {
    id: root
    objectName: "window"
    property bool initialLeftLayout: false
    property bool customClose: false
    property bool noneClose: false
    property int customCollapseCount: 0
    property int customStopCount: 0
    property int nativeCloseAcceptedCount: 0
    readonly property int topLayout: Enums.windowType.title_bar_top
    readonly property int leftLayout: Enums.windowType.title_bar_left
    readonly property int noneAnimationType: Enums.animation.none
    readonly property int noShadow: Enums.windowShadow.mode_none
    readonly property int qmlShadow: Enums.windowShadow.mode_qml
    readonly property int nativeShadow: Enums.windowShadow.mode_native
    readonly property int navPanelMinWidth: Enums.window.navPanelMinWidth
    readonly property int dividerWidth: Enums.border.thin
    readonly property int resizeDelay: Enums.window.resizeHandlesDelayMs

    width: 720
    height: 520
    visible: true
    shadowMode: Enums.windowShadow.mode_none
    windowTitle: "WindowsCore Contract"
    windowIcon: Qt.resolvedUrl("../../examples/resources/image/avatar/avatar.png")
    titleBarPosition: initialLeftLayout ? leftLayout : topLayout
    closeAnimationType: noneClose
        ? Enums.animation.none
        : (customClose ? Enums.animation.custom : Enums.animation.lazy_circle)
    closeAnimation: customClose ? customCloseComponent : null

    onNativeCloseAccepted: nativeCloseAcceptedCount += 1

    Item {
        objectName: "contentProbe"
        width: 20
        height: 20
    }

    leftPanelContent: [
        Item {
            objectName: "leftProbe"
            width: 16
            height: 16
        }
    ]

    Component {
        id: customCloseComponent

        Item {
            property bool active: false
            property bool running: false
            property bool collapsing: false
            property bool collapsed: false
            property real progress: 0

            signal collapseStarted()
            signal collapseFinished()
            signal expandStarted()
            signal expandFinished()

            function collapse(sourceItem) {
                root.customCollapseCount += 1
                active = true
                running = true
                collapsing = true
                collapseStarted()
                progress = 1
                sourceItem.visible = false
                collapsed = true
                running = false
                active = false
                collapseFinished()
                return true
            }

            function expand(sourceItem) {
                sourceItem.visible = true
                collapsed = false
                expandStarted()
                expandFinished()
                return true
            }

            function stop() {
                root.customStopCount += 1
                active = false
                running = false
                collapsed = false
            }
        }
    }
}
"""


class _FakeNativeWindow(QObject):
    def __init__(self, events, parent=None):
        super().__init__(parent)
        self._events = events

    @Slot(QObject, result=bool)
    def finalizeAttach(self, _window):
        self._events.append("native-finalized")
        return True

    @Slot(QObject, result=bool)
    def detach(self, _window):
        return True

    @Slot(QObject, result=bool)
    def requestMaximize(self, window):
        self._events.append("native-maximize")
        window.showMaximized()
        return True

    @Slot(QObject, result=bool)
    def requestRestore(self, window):
        self._events.append("native-restore")
        window.showNormal()
        return True


class _FakeWindowHelper(QObject):
    def __init__(self, events, parent=None):
        super().__init__(parent)
        self._events = events

    @Slot(str)
    def setAppIcon(self, icon):
        assert icon
        self._events.append("icon")


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2200) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _resize_areas(window: QQuickWindow) -> list[QQuickItem]:
    return [
        item
        for item in _visual_descendants(window.contentItem())
        if item.metaObject().className().startswith("ResizeArea")
        and item.metaObject().indexOfProperty("edge") >= 0
    ]


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _create_scene(
    monkeypatch,
    *,
    initial_left_layout: bool = False,
    custom_close: bool = False,
    none_close: bool = False,
):
    engine = QQmlApplicationEngine()
    startup_events = []
    native_window = _FakeNativeWindow(startup_events, engine)
    window_helper = _FakeWindowHelper(startup_events, engine)
    monkeypatch.setattr(
        window_services_module, "get_native_window_hook", lambda: native_window
    )
    monkeypatch.setattr(
        window_services_module, "get_window_helper", lambda: window_helper
    )
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.createWithInitialProperties(
        {
            "initialLeftLayout": initial_left_layout,
            "customClose": custom_close,
            "noneClose": none_close,
        },
        engine.rootContext(),
    )
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    content = window.findChild(QQuickItem, "contentContainer")
    content_probe = window.findChild(QQuickItem, "contentProbe")
    left_probe = window.findChild(QQuickItem, "leftProbe")
    assert (
        content is not None
        and content_probe is not None
        and left_probe is not None
    )
    assert content_probe.parentItem() is content
    return (
        engine,
        component,
        window,
        content,
        left_probe,
        warnings,
        startup_events,
    )


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def test_windows_core_top_left_and_qml_shadow_geometry(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        content,
        left_probe,
        warnings,
        startup_events,
    ) = _create_scene(monkeypatch)
    try:
        icon_event = "icon"
        assert _wait_for(lambda: startup_events.count(icon_event) == 2)
        first_icon_index = startup_events.index(icon_event)
        native_index = startup_events.index("native-finalized")
        second_icon_index = len(startup_events) - 1 - startup_events[::-1].index(
            icon_event
        )
        assert first_icon_index < native_index < second_icon_index
        assert window.title() == "WindowsCore Contract"
        assert window.property("titleBarPosition") == window.property("topLayout")
        assert window.property("margin") == 0
        assert content.y() == pytest.approx(window.property("titleBarHeight"))
        assert content.x() == pytest.approx(0)
        assert not left_probe.parentItem().parentItem().isVisible()

        window.setProperty("titleBarPosition", window.property("leftLayout"))
        assert _wait_for(lambda: content.y() == pytest.approx(0))
        expected_left = max(
            window.property("leftPanelWidth"), window.property("navPanelMinWidth")
        ) + window.property("dividerWidth")
        assert content.x() == pytest.approx(expected_left)
        assert left_probe.parentItem().parentItem().isVisible()

        window.setProperty("shadowMode", window.property("qmlShadow"))
        assert _wait_for(
            lambda: window.property("margin") == window.property("shadowSize")
            and window.property("_animScale") == 1.0
            and window.property("_animOpacity") == 1.0
        )
        mapped = content.mapToItem(window.contentItem(), QPointF())
        assert mapped.x() == pytest.approx(
            window.property("margin") + expected_left, abs=0.001
        )
        assert mapped.y() == pytest.approx(window.property("margin"), abs=0.001)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_deferred_resize_handles_load_once(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        content,
        left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch)
    try:
        assert not window.property("_resizeHandlesReady")
        assert _wait_for(lambda: bool(window.property("_resizeHandlesReady")))
        assert _wait_for(lambda: len(_resize_areas(window)) == 4)
        resize_areas = _resize_areas(window)
        assert len(resize_areas) == 4
        _pump(window.property("resizeDelay") // 4)
        assert len(_resize_areas(window)) == 4
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_right_title_chrome_is_layout_scoped(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch)
    try:
        loader = window.findChild(QObject, "rightTitleChromeLoader")
        assert loader is not None
        assert not loader.property("active")
        assert window.findChild(QObject, "rightTitleChrome") is None

        window.setProperty("titleBarPosition", window.property("leftLayout"))
        chrome = window.findChild(QQuickItem, "rightTitleChrome")
        buttons = window.findChild(QQuickItem, "captionButtonsRight")
        drag_area = window.findChild(QQuickItem, "rightTitleBarDragArea")
        assert chrome is not None and buttons is not None and drag_area is not None
        assert buttons.x() == pytest.approx(
            window.width() - window.property("captionButtonWidth") * 3
        )
        assert drag_area.x() == pytest.approx(
            max(
                window.property("leftPanelWidth"),
                window.property("navPanelMinWidth"),
            )
            + window.property("dividerWidth")
        )
        assert drag_area.width() == pytest.approx(buttons.x() - drag_area.x())

        maximize_center = buttons.mapToItem(
            window.contentItem(),
            QPointF(
                window.property("captionButtonWidth") * 1.5,
                window.property("captionButtonHeight") / 2,
            ),
        )
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(maximize_center.x()), round(maximize_center.y())),
        )
        assert _wait_for(
            lambda: window.visibility() == QWindow.Visibility.Maximized
        )
        window.showNormal()
        assert _wait_for(lambda: window.visibility() == QWindow.Visibility.Windowed)

        window.setProperty("titleBarPosition", window.property("topLayout"))
        assert _wait_for(
            lambda: window.findChild(QObject, "rightTitleChrome") is None
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_initial_left_title_chrome_is_ready(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch, initial_left_layout=True)
    try:
        loader = window.findChild(QObject, "rightTitleChromeLoader")
        assert loader is not None and loader.property("active")
        assert window.findChild(QObject, "rightTitleChrome") is not None
        assert window.findChild(QObject, "captionButtonsRight") is not None
        assert window.findChild(QObject, "rightTitleBarDragArea") is not None
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


@pytest.mark.parametrize(
    ("initial_left_layout", "drag_area_name"),
    (
        (False, "topTitleBarDragArea"),
        (True, "leftTitleBarDragArea"),
        (True, "rightTitleBarDragArea"),
    ),
)
def test_windows_core_titlebar_double_click_routes_native_transition(
    monkeypatch, qapp, initial_left_layout, drag_area_name
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        startup_events,
    ) = _create_scene(
        monkeypatch, initial_left_layout=initial_left_layout
    )
    try:
        drag_area = window.findChild(QQuickItem, drag_area_name)
        assert drag_area is not None, drag_area_name

        def double_click_drag_area():
            center = drag_area.mapToItem(
                window.contentItem(),
                QPointF(drag_area.width() / 2, drag_area.height() / 2),
            )
            QTest.mouseDClick(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                QPoint(round(center.x()), round(center.y())),
            )

        double_click_drag_area()
        assert _wait_for(
            lambda: window.visibility() == QWindow.Visibility.Maximized
        )
        double_click_drag_area()
        assert _wait_for(
            lambda: window.visibility() == QWindow.Visibility.Windowed
        )
        assert startup_events.count("native-maximize") == 1
        assert startup_events.count("native-restore") == 1
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_native_close_reuses_lazy_circle_exit_animation(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch)
    try:
        assert _wait_for(
            lambda: window.opacity() == pytest.approx(1)
            and window.property("_animOpacity") == pytest.approx(1)
            and window.property("_animScale") == pytest.approx(1)
        )

        transition = window.findChild(QObject, "windowClosePageTransition")
        assert transition is not None
        assert transition.property("animationType") == 7

        # The first native/QWindow close leaves the current onClosing delivery,
        # then reuses PageTransition before the accepted close.
        # 首次原生/QWindow 关闭退出当前 onClosing 分发, 再复用 PageTransition 后真实关闭。
        assert window.close() is False
        assert window.property("_closeInProgress") is True
        assert window.property("nativeCloseAcceptedCount") == 0

        assert _wait_for(
            lambda: window.property("nativeCloseAcceptedCount") == 1
            and not window.isVisible(),
            timeout_ms=500,
        )
        assert window.opacity() == pytest.approx(1)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_close_collapse_reaches_zero_radius_before_teardown(
    monkeypatch, qapp
):
    """退场必须收紧到零半径才移除窗口，且中途不得跳步。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch)
    try:
        transition = window.findChild(QObject, "windowClosePageTransition")
        assert transition is not None

        # The exit must not inherit the page-switch collapse pacing.
        # 退场不得沿用页面切换的收紧节奏。
        page_cover_duration = 300
        assert transition.property("coverDuration") > page_cover_duration
        assert transition.property("coverEasing") == int(
            QEasingCurve.Type.InOutQuad.value
        )

        # Offscreen presents almost no frames during the collapse, so the
        # per-frame trajectory is not observable here; assert the ordering
        # invariant instead and leave pacing to the visible D3D11 probe
        # (scripts/manual/window_close_collapse_probe.py). offscreen 在收紧
        # 期间几乎不上屏, 逐帧轨迹在此不可观测; 这里只断言时序不变量, 节奏交给
        # 可见 D3D11 探针验收。
        collapse_endpoints = []
        transition.collapseFinished.connect(
            lambda: collapse_endpoints.append(
                (
                    float(transition.property("progress")),
                    float(transition.property("revealRadiusPixels")),
                    bool(window.isVisible()),
                )
            )
        )
        visibility_progress = []
        window.visibleChanged.connect(
            lambda: visibility_progress.append(
                (
                    bool(window.isVisible()),
                    float(transition.property("progress")),
                )
            )
        )

        assert window.close() is False
        assert _wait_for(
            lambda: window.property("nativeCloseAcceptedCount") == 1
            and not window.isVisible(),
            timeout_ms=2000,
        )

        # The collapse must finish at the zero endpoint, and it must finish
        # while the window is still on screen. 收紧必须走到零终点, 且必须在窗口
        # 仍在屏上时完成。
        assert collapse_endpoints
        end_progress, end_radius, visible_at_end = collapse_endpoints[-1]
        assert end_progress == pytest.approx(0, abs=1e-6)
        assert end_radius == pytest.approx(0, abs=1e-6)
        assert visible_at_end is True
        # Teardown may only happen after the collapse reached zero.
        # 只有收紧到零之后才允许移除窗口。
        hide_events = [
            progress for visible, progress in visibility_progress if not visible
        ]
        assert hide_events
        assert hide_events[-1] == pytest.approx(0, abs=1e-6)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_close_collapse_drops_native_shadow(monkeypatch, qapp):
    """收紧期间必须撤掉原生 DWM 阴影，否则整窗矩形阴影留在圆外。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    shadow_manager = window_services_module.getShadowManager()
    calls = []
    for name in ("enableShadowForWindow", "disableShadowForWindow"):
        original = getattr(shadow_manager, name)

        def _spy(window, _name=name, _original=original):
            calls.append(_name)
            return _original(window)

        monkeypatch.setattr(shadow_manager, name, _spy)

    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch)
    try:
        # The native shadow is a DWM policy on the hwnd; no QML layer mask can
        # clip it, so it must be switched off for the collapse itself. The scene
        # defaults to mode_none, so opt in or the assertion is vacuous.
        # 原生阴影是 hwnd 上的 DWM 策略, QML 遮罩裁不到, 必须在收紧时关掉。场景默认
        # mode_none, 必须显式打开, 否则断言是空的。
        window.setProperty("shadowMode", window.property("nativeShadow"))
        assert _wait_for(lambda: window.property("_useNativeShadow") is True)
        calls.clear()

        assert window.close() is False
        assert "disableShadowForWindow" in calls
        assert _wait_for(
            lambda: window.property("nativeCloseAcceptedCount") == 1
            and not window.isVisible(),
            timeout_ms=2000,
        )
        # The collapse must not re-enable it midway.
        # 收紧过程中不得又把它打开。
        assert "enableShadowForWindow" not in calls
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_cancelled_close_restores_native_shadow(monkeypatch, qapp):
    """取消关闭必须把原生阴影装回去。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    shadow_manager = window_services_module.getShadowManager()
    calls = []
    for name in ("enableShadowForWindow", "disableShadowForWindow"):
        original = getattr(shadow_manager, name)

        def _spy(window, _name=name, _original=original):
            calls.append(_name)
            return _original(window)

        monkeypatch.setattr(shadow_manager, name, _spy)

    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch)
    try:
        window.setProperty("shadowMode", window.property("nativeShadow"))
        assert _wait_for(lambda: window.property("_useNativeShadow") is True)
        calls.clear()

        # A cancelled close leaves the window on screen, so the shadow dropped
        # for the collapse has to come back. This scene has no way to refuse a
        # close, so drive the cancel entry point directly.
        # 取消的关闭会让窗口留在屏上, 为收紧撤掉的阴影必须装回。本场景无法拒绝关闭,
        # 故直接驱动取消入口。
        assert QMetaObject.invokeMethod(window, "_startAcceptedClose")
        assert window.property("_closeInProgress") is True
        assert calls == ["disableShadowForWindow"]

        assert QMetaObject.invokeMethod(window, "_cancelCloseRequest")
        assert window.property("_closeInProgress") is False
        assert window.isVisible()
        assert calls[-1] == "enableShadowForWindow"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_close_collapse_clips_unmasked_shadow_layer(monkeypatch, qapp):
    """收紧期间必须撤掉未被遮罩的阴影层，否则圆外残留矩形留白。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch)
    try:
        # The QML shadow host is a sibling of the masked frame layer, so the
        # close circle's layer effect never clips it. It fills the window with
        # an opaque windowColor rect, which shows through as a rectangular
        # blank once the circle shrinks past it.
        # QML 阴影宿主是被遮罩帧层的兄弟节点, 关闭圆环的 layer effect 裁不到它。它
        # 以不透明 windowColor 矩形铺满窗口, 圆收过去后就露成矩形留白。
        shadow_host = window.findChild(QObject, "windowQmlShadowHost")
        assert shadow_host is not None
        # The scene defaults to the native shadow, which leaves this host
        # inactive and would make the assertion below vacuous. Force the QML
        # shadow so the unmasked layer really exists.
        # 场景默认走原生阴影, 该宿主不激活, 下面的断言会变成空断言。强制 QML 阴影,
        # 让未遮罩层真实存在。
        window.setProperty("shadowMode", _WINDOW_SHADOW_MODE_QML)
        assert _wait_for(lambda: shadow_host.property("active") is True)

        transition = window.findChild(QObject, "windowClosePageTransition")
        assert transition is not None

        samples = []

        def _sample():
            samples.append(
                (
                    float(transition.property("progress")),
                    bool(shadow_host.property("active")),
                )
            )

        sampler = QTimer()
        sampler.setInterval(8)
        sampler.timeout.connect(_sample)
        sampler.start()

        assert window.close() is False
        assert _wait_for(
            lambda: window.property("nativeCloseAcceptedCount") == 1
            and not window.isVisible(),
            timeout_ms=2000,
        )
        sampler.stop()

        # Every sample taken while the circle was still open must show the
        # unmasked layer already gone. 圆尚未收完时的每个采样都必须显示未遮罩层
        # 已经撤掉。
        assert samples
        still_active = [
            progress for progress, active in samples if active
        ]
        assert still_active == []
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_close_collapse_easing_spreads_motion_evenly():
    """收紧缓动必须把运动均匀分布，不得把大半距离压到末尾几帧。"""
    frame_count = 12
    # The curve replaced everywhere, kept here as the contrast case.
    # 已被全面替换掉的曲线, 保留作对照。
    rejected = QEasingCurve(QEasingCurve.Type.InCubic)
    shared = QEasingCurve(QEasingCurve.Type.InOutQuad)

    def _radius_series(curve):
        # progress runs 1 -> 0, radius scales with progress.
        # progress 由 1 走到 0, 半径随 progress 线性缩放。
        return [
            1.0 - curve.valueForProgress(index / (frame_count - 1))
            for index in range(frame_count)
        ]

    def _max_step(series):
        return max(
            earlier - later for earlier, later in zip(series, series[1:])
        )

    def _half_at(series):
        return next(
            index / (frame_count - 1)
            for index, radius in enumerate(series)
            if radius <= 0.5
        )

    rejected_series = _radius_series(rejected)
    shared_series = _radius_series(shared)

    # The rejected curve reaches half radius only near the very end, leaving the
    # whole second half to the last frames. 被弃用的曲线直到接近末尾才收到半径
    # 一半, 把后半程全部压给最后几帧。
    assert _half_at(rejected_series) > 0.7
    assert _half_at(shared_series) == pytest.approx(0.5, abs=0.1)
    assert _max_step(shared_series) < _max_step(rejected_series)
    assert _max_step(shared_series) < 0.2


def test_windows_core_close_accepts_custom_page_transition(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch, custom_close=True)
    try:
        transition = window.findChild(QObject, "windowClosePageTransition")
        assert transition is not None
        assert transition.property("animationType") == 8
        assert window.property("customCollapseCount") == 0

        assert window.close() is False
        assert _wait_for(
            lambda: window.property("customCollapseCount") == 1
            and window.property("nativeCloseAcceptedCount") == 1
            and not window.isVisible(),
            timeout_ms=500,
        )
        # PageTransition stops any previous operation before starting collapse.
        # PageTransition 会先停止已有操作, 再开始本次收紧。
        assert window.property("customStopCount") == 1
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_close_accepts_none_transition(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch, none_close=True)
    try:
        transition = window.findChild(QObject, "windowClosePageTransition")
        assert transition is not None
        assert transition.property("animationType") == window.property(
            "noneAnimationType"
        )

        assert window.close() is False
        assert window.property("nativeCloseAcceptedCount") == 0
        assert _wait_for(
            lambda: window.property("nativeCloseAcceptedCount") == 1
            and not window.isVisible(),
            timeout_ms=500,
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_source_conventions_and_timing_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    frame_source = WINDOW_FRAME_PATH.read_text(encoding="utf-8")
    resize_timer_source = RESIZE_HANDLES_TIMER_PATH.read_text(encoding="utf-8")
    drag_handle_source = WINDOW_DRAG_HANDLE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "WindowsResizeHandlesTimer {" in source
    assert "id: _resizeHandlesTimer" in source
    assert "host: window" in source
    assert "\n    Timer {" not in source
    assert "Timer {" in resize_timer_source
    assert "required property var host" in resize_timer_source
    assert "interval: Enums.window.resizeHandlesDelayMs" in resize_timer_source
    assert "host._resizeHandlesReady = true" in resize_timer_source
    assert "_animationStartTimer" not in source
    assert "interval: 100" not in source
    assert "interval: 1200" not in source
    assert "window.showMaximized()" not in source
    assert "window.showNormal()" not in source
    assert "WindowsCoreFrame {" in source
    assert "WindowDragHandle {" not in source
    window_frame_index = frame_source.index("id: windowFrame")
    window_ticket_paper_index = frame_source.index(
        'objectName: "windowTicketPaper"'
    )
    title_bar_index = frame_source.index("id: titleBar")
    assert window_frame_index < window_ticket_paper_index < title_bar_index
    assert "TicketPaper {" in frame_source[
        window_frame_index:title_bar_index
    ]
    assert frame_source.count("WindowDragHandle {") == 3
    assert "window.startSystemMove()" not in source
    assert "property bool enableDrag: true" in drag_handle_source
    assert "property bool _doubleClickPending: false" in drag_handle_source
    assert "onDoubleClicked:" in drag_handle_source
    assert "onReleased: root._applyPendingDoubleClick()" in drag_handle_source
    assert "NativeWindow.requestMaximize(win)" in drag_handle_source
    assert "NativeWindow.requestRestore(win)" in drag_handle_source
    profile_start = source.index("function profileTime(msg)")
    profile_end = source.index("function profileDetail(msg)", profile_start)
    assert "if (!_startupProfilingVerboseActive) return" in source[
        profile_start:profile_end
    ]
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    assert "readonly property int resizeHandlesDelayMs: 1200" in metrics


def test_leaf_startup_diagnostics_do_not_attach_to_default_object_tree():
    windows_core = SOURCE_PATH.read_text(encoding="utf-8")
    assert "function profileDetail(msg)" in windows_core
    assert "Component.onCompleted: window.profileDetail" not in windows_core
    assert "profileTarget" not in windows_core

    for source_path in STARTUP_DIAGNOSTIC_PATHS:
        source = source_path.read_text(encoding="utf-8")
        assert "profileDetail" not in source, source_path
        assert "profileTarget" not in source, source_path

    builder = WINDOW_BUILDER_PATH.read_text(encoding="utf-8")
    assert "profileDetail" not in builder


def test_window_animation_helper_source_conventions_and_dead_paths():
    source = ANIMATION_HELPER_PATH.read_text(encoding="utf-8")
    close_frame_waiter_source = WINDOW_CLOSE_FRAME_WAITER_PATH.read_text(
        encoding="utf-8"
    )
    path = PurePosixPath(ANIMATION_HELPER_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "animatedMinimizeWithForward" not in source
    assert "handleVisibilityChange" not in source
    assert "WindowCloseDissolve" not in source
    assert "closeEffectLoader" not in source
    assert "prewarmCloseAnimation" not in source
    assert "animatedClose" not in source
    assert "animHelper.handleVisibilityChange" not in SOURCE_PATH.read_text(
        encoding="utf-8"
    )
    windows_core_source = SOURCE_PATH.read_text(encoding="utf-8")
    assert 'import "./controls/navigation"' in windows_core_source
    assert "property int closeAnimationType: Enums.animation.lazy_circle" in windows_core_source
    assert "property Component closeAnimation: null" in windows_core_source
    assert "property bool _closeSourceWasVisible: true" in windows_core_source
    assert "property bool _closeCompletionPending: false" in windows_core_source
    assert "PageTransition {" in windows_core_source
    assert 'objectName: "windowClosePageTransition"' in windows_core_source
    assert "animationType: window.closeAnimationType" in windows_core_source
    assert "customAnimation: window.closeAnimation" in windows_core_source
    assert "collapseToCenter: true" in windows_core_source
    # The collapse pacing is shared with page switch, so the exit must inherit
    # the facade default rather than pin its own duration or easing. Measured on
    # a real display, both sites produce identical pacing.
    # 收紧节奏与页面切换共用, 因此退场应继承门面默认值, 不得自己钉死时长或缓动。
    # 真机实测两处节奏完全相同。
    assert "coverDuration:" not in windows_core_source
    assert "coverEasing:" not in windows_core_source
    assert "closeTransition.collapse(windowFrameLayer)" in windows_core_source
    assert "windowFrameLayer.visible = _closeSourceWasVisible" in windows_core_source
    assert "Qt.callLater(window._armAcceptedClose)" in windows_core_source
    assert "function _handleCloseFrameEnd()" in windows_core_source
    assert "closeFrameWaiter.arm()" in windows_core_source
    waiter_path = PurePosixPath(
        WINDOW_CLOSE_FRAME_WAITER_PATH.relative_to(ROOT).as_posix()
    )
    waiter_violations = scan_source_text(close_frame_waiter_source, waiter_path)
    assert [
        violation
        for violation in waiter_violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "function onAfterFrameEnd()" in close_frame_waiter_source
    assert "Timer {" not in close_frame_waiter_source
    assert "interval:" not in close_frame_waiter_source
    assert "animHelper.animatedClose()" not in windows_core_source


def test_window_close_dissolve_artifacts_and_api_are_removed():
    assert [path for path in REMOVED_CLOSE_EFFECT_PATHS if path.exists()] == []
    windows_core_source = SOURCE_PATH.read_text(encoding="utf-8")
    caption_source = CAPTION_BUTTON_PATH.read_text(encoding="utf-8")
    metrics_source = METRICS_PATH.read_text(encoding="utf-8")
    enums_source = ENUMS_PATH.read_text(encoding="utf-8")
    assert "prewarmCloseAnimation" not in windows_core_source
    assert "prewarmCloseAnimation" not in caption_source
    assert "windowCloseMetrics" not in enums_source
    assert "readonly property QtObject windowClose" not in metrics_source


def test_window_leaf_source_conventions_and_icon_delay_token():
    for source_path in WINDOW_LEAF_PATHS:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009"}
        ] == []
    window_icon = (
        ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowIcon.qml"
    ).read_text(encoding="utf-8")
    icon_timer = WINDOW_ICON_DEFERRED_TIMER_PATH.read_text(encoding="utf-8")
    icon_timer_path = PurePosixPath(
        WINDOW_ICON_DEFERRED_TIMER_PATH.relative_to(ROOT).as_posix()
    )
    icon_timer_violations = scan_source_text(icon_timer, icon_timer_path)
    assert [
        violation
        for violation in icon_timer_violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "WindowIconDeferredLoadTimer {" in window_icon
    assert "host: root" in window_icon
    assert "\n    Timer {" not in window_icon
    assert "onTriggered: {" not in window_icon
    assert "required property var host" in icon_timer
    assert 'objectName: "windowIconDeferredLoadTimer"' in icon_timer
    assert "interval: Enums.window.iconDeferredLoadDelayMs" in icon_timer
    assert "repeat: false" in icon_timer
    assert "onTriggered: host._deferredLoadReady = true" in icon_timer
    assert "interval: 1" not in window_icon
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    assert "readonly property int iconDeferredLoadDelayMs: 1" in metrics
