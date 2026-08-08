# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowsCore geometry and lifecycle contracts. 窗口核心几何与生命周期合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
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

import prismqml.python.core.window_helper as window_helper_module
import prismqml.python.window as window_module
from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "prismqml" / "PrismQML" / "WindowsCore.qml"
ANIMATION_HELPER_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowAnimationHelper.qml"
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
        "WindowCloseDissolve.qml",
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
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "windows-core-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

WindowsCore {
    objectName: "window"
    property bool initialLeftLayout: false
    property int nativeCloseAcceptedCount: 0
    readonly property int topLayout: Enums.windowType.title_bar_top
    readonly property int leftLayout: Enums.windowType.title_bar_left
    readonly property int noShadow: Enums.windowShadow.mode_none
    readonly property int qmlShadow: Enums.windowShadow.mode_qml
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


def _create_scene(monkeypatch, *, initial_left_layout: bool = False):
    engine = QQmlApplicationEngine()
    startup_events = []
    native_window = _FakeNativeWindow(startup_events, engine)
    window_helper = _FakeWindowHelper(startup_events, engine)
    monkeypatch.setattr(
        window_module, "get_native_window_hook", lambda: native_window
    )
    monkeypatch.setattr(
        window_helper_module, "get_window_helper", lambda: window_helper
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
        {"initialLeftLayout": initial_left_layout}, engine.rootContext()
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


def test_windows_core_native_close_waits_for_exit_animation(monkeypatch, qapp):
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

        # The first native/QWindow close is intercepted while the dissolve runs.
        # 首次原生/QWindow 关闭会在渐隐期间被拦截。
        assert window.close() is False
        assert window.isVisible()
        assert window.property("_closeInProgress") is True
        assert window.property("nativeCloseAcceptedCount") == 0

        # WindowAnimationHelper closes the QWindow only after the fade completes.
        # 动画完成后 WindowAnimationHelper 才真正关闭 QWindow。
        assert _wait_for(
            lambda: window.property("nativeCloseAcceptedCount") == 1
            and not window.isVisible(),
            timeout_ms=3000,
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_source_conventions_and_timing_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    drag_handle_source = WINDOW_DRAG_HANDLE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "interval: Enums.window.resizeHandlesDelayMs" in source
    assert "_animationStartTimer" not in source
    assert "interval: 100" not in source
    assert "interval: 1200" not in source
    assert "window.showMaximized()" not in source
    assert "window.showNormal()" not in source
    assert source.count("WindowDragHandle {") == 3
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
    path = PurePosixPath(ANIMATION_HELPER_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "animatedMinimizeWithForward" not in source
    assert "handleVisibilityChange" not in source
    assert "animHelper.handleVisibilityChange" not in SOURCE_PATH.read_text(
        encoding="utf-8"
    )


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
    window_icon = WINDOW_LEAF_PATHS[2].read_text(encoding="utf-8")
    assert "interval: Enums.window.iconDeferredLoadDelayMs" in window_icon
    assert "interval: 1" not in window_icon
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    assert "readonly property int iconDeferredLoadDelayMs: 1" in metrics
