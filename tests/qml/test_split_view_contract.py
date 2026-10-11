# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SplitView display mode and interaction contracts. SplitView 显示模式与交互合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
LAYOUT_DIR = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "containers" / "Layout"
)
SOURCE_PATHS = [
    LAYOUT_DIR / "SplitView.qml",
    LAYOUT_DIR / "_internal" / "SplitViewContent.qml",
]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "split-view-contract.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/Layout"

Window {
    id: root
    objectName: "window"
    width: 700
    height: 500
    visible: false

    property int openedCount: 0
    property int closedCount: 0
    property int dismissCount: 0
    property real lastResizedLength: -1

    function useOverlay() {
        split.displayMode = Enums.flow.split_display_overlay
    }

    function useInline() {
        split.displayMode = Enums.flow.split_display_inline
    }

    function useCompactOverlay() {
        split.displayMode = Enums.flow.split_display_compact_overlay
    }

    function useCompactInline() {
        split.displayMode = Enums.flow.split_display_compact_inline
    }

    function openPane() { split.openPane() }
    function closePane() { split.closePane() }
    function togglePane() { split.togglePane() }
    function setPaneLengthMinimum() { split.setPaneLength(10) }
    function setPaneLengthHuge() { split.setPaneLength(1000) }
    function setPaneLengthInvalid() { split.setPaneLength(NaN) }

    SplitView {
        id: split
        objectName: "splitView"
        x: 20
        y: 20
        width: 400
        height: 300
        openPaneLength: 200
        compactPaneLength: 48
        paneMinimumSize: 60

        onPaneOpening: root.openedCount++
        onPaneClosed: root.closedCount++
        onLightDismissed: root.dismissCount++
        onPaneResized: (length) => root.lastResizedLength = length

        Item { objectName: "mainContent"; anchors.fill: parent }

        paneContent: Item { objectName: "paneContent"; anchors.fill: parent }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 900) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


def _create_scene():
    engine = QQmlApplicationEngine()
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
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    _pump()
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def split_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        yield window, warnings, windows_before
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def _split(window) -> QQuickItem:
    split = window.findChild(QQuickItem, "splitView")
    assert split is not None
    return split


def _pane_width(window) -> float:
    pane = _split(window).findChild(QQuickItem, "splitViewPane")
    assert pane is not None
    return pane.width()


def test_split_view_sources_follow_conventions():
    for source_path in SOURCE_PATHS:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        assert scan_source_text(source, path) == []


def test_split_view_keeps_the_visual_tree_in_internal():
    entry = SOURCE_PATHS[0].read_text(encoding="utf-8")
    content = SOURCE_PATHS[1].read_text(encoding="utf-8")
    assert len(entry.splitlines()) < 300
    assert "required property Item host" in content
    assert "required property Item host" not in entry
    for marker in ("Rectangle {", "MouseArea {", "Icon {"):
        assert marker not in entry


def test_split_view_display_modes_drive_pane_and_content_offset(split_scene):
    window, warnings, windows_before = split_scene
    split = _split(window)

    assert QMetaObject.invokeMethod(window, "useOverlay")
    assert split.property("paneExtent") == pytest.approx(0)
    assert split.property("contentOffset") == pytest.approx(0)
    assert split.property("isPaneVisible") is False
    assert QMetaObject.invokeMethod(window, "openPane")
    assert split.property("paneExtent") == pytest.approx(200)
    assert split.property("contentOffset") == pytest.approx(0)
    assert split.property("isPaneVisible") is True
    assert split.property("isLightDismissActive") is True

    assert QMetaObject.invokeMethod(window, "useInline")
    assert split.property("paneExtent") == pytest.approx(200)
    assert split.property("contentOffset") == pytest.approx(200)
    assert split.property("isLightDismissActive") is False
    assert QMetaObject.invokeMethod(window, "closePane")
    assert split.property("paneExtent") == pytest.approx(0)
    assert split.property("contentOffset") == pytest.approx(0)

    assert QMetaObject.invokeMethod(window, "useCompactOverlay")
    assert split.property("paneExtent") == pytest.approx(48)
    assert split.property("contentOffset") == pytest.approx(0)
    assert split.property("isPaneVisible") is True
    assert QMetaObject.invokeMethod(window, "openPane")
    assert split.property("paneExtent") == pytest.approx(200)
    assert split.property("contentOffset") == pytest.approx(0)

    assert QMetaObject.invokeMethod(window, "useCompactInline")
    assert split.property("paneExtent") == pytest.approx(200)
    assert split.property("contentOffset") == pytest.approx(200)
    assert QMetaObject.invokeMethod(window, "closePane")
    assert split.property("paneExtent") == pytest.approx(48)
    assert split.property("contentOffset") == pytest.approx(48)

    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_split_view_renders_pane_and_content_hosts(split_scene):
    window, warnings, windows_before = split_scene
    split = _split(window)
    assert QMetaObject.invokeMethod(window, "useInline")
    assert QMetaObject.invokeMethod(window, "openPane")

    content_host = split.findChild(QQuickItem, "splitViewContentHost")
    pane_host = split.findChild(QQuickItem, "splitViewPaneHost")
    main_content = split.findChild(QQuickItem, "mainContent")
    pane_content = split.findChild(QQuickItem, "paneContent")
    assert content_host is not None and pane_host is not None
    assert main_content is not None and pane_content is not None
    assert main_content.parentItem() is content_host
    assert pane_content.parentItem() is pane_host

    assert _wait_for(lambda: _pane_width(window) == pytest.approx(200))
    assert _wait_for(lambda: content_host.x() == pytest.approx(200))
    assert content_host.width() == pytest.approx(200)
    assert content_host.height() == pytest.approx(300)
    assert pane_host.width() == pytest.approx(200)
    assert pane_host.height() == pytest.approx(300)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_split_view_light_dismiss_only_closes_overlay_panes(split_scene):
    window, warnings, windows_before = split_scene
    window.show()
    _pump()
    split = _split(window)
    scrim = split.findChild(QQuickItem, "splitViewDismissScrim")
    assert scrim is not None

    assert QMetaObject.invokeMethod(window, "useOverlay")
    assert QMetaObject.invokeMethod(window, "openPane")
    _pump()
    assert scrim.isVisible()
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, pos=QPoint(370, 270)
    )
    _pump()
    assert split.property("paneOpen") is False
    assert window.property("dismissCount") == 1

    assert QMetaObject.invokeMethod(window, "useInline")
    assert QMetaObject.invokeMethod(window, "openPane")
    _pump()
    assert not scrim.isVisible()
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, pos=QPoint(370, 270)
    )
    _pump()
    assert split.property("paneOpen") is True
    assert window.property("dismissCount") == 1

    window.hide()
    _pump()
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_split_view_resize_drag_is_bidirectional(split_scene):
    window, warnings, windows_before = split_scene
    window.show()
    _pump()
    split = _split(window)
    assert QMetaObject.invokeMethod(window, "useInline")
    assert QMetaObject.invokeMethod(window, "openPane")
    _pump()

    resize_area = split.findChild(QQuickItem, "splitViewResizeArea")
    assert resize_area is not None
    assert resize_area.isVisible()

    handle_x = 20 + split.property("openPaneLength") - 4
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, pos=QPoint(int(handle_x) + 4, 170)
    )
    QTest.mouseMove(window, QPoint(int(handle_x) + 54, 170), delay=10)
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, pos=QPoint(int(handle_x) + 54, 170)
    )
    _pump()
    assert split.property("openPaneLength") == pytest.approx(250)
    assert window.property("lastResizedLength") == pytest.approx(250)

    handle_x = 20 + split.property("openPaneLength") - 4
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, pos=QPoint(int(handle_x) + 4, 170)
    )
    QTest.mouseMove(window, QPoint(int(handle_x) - 36, 170), delay=10)
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, pos=QPoint(int(handle_x) - 36, 170)
    )
    _pump()
    assert split.property("openPaneLength") == pytest.approx(210)
    assert window.property("lastResizedLength") == pytest.approx(210)
    assert _wait_for(lambda: _pane_width(window) == pytest.approx(210))

    window.hide()
    _pump()
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_split_view_signals_and_pane_length_clamping(split_scene):
    window, warnings, windows_before = split_scene
    split = _split(window)
    assert QMetaObject.invokeMethod(window, "useInline")

    assert QMetaObject.invokeMethod(window, "openPane")
    assert window.property("openedCount") == 1
    assert QMetaObject.invokeMethod(window, "togglePane")
    assert split.property("paneOpen") is False
    assert window.property("closedCount") == 1

    assert QMetaObject.invokeMethod(window, "setPaneLengthMinimum")
    assert split.property("openPaneLength") == 60
    assert window.property("lastResizedLength") == pytest.approx(60)
    assert QMetaObject.invokeMethod(window, "setPaneLengthHuge")
    assert split.property("openPaneLength") == 400
    assert window.property("lastResizedLength") == pytest.approx(400)
    assert QMetaObject.invokeMethod(window, "setPaneLengthInvalid")
    assert split.property("openPaneLength") == 400
    assert QMetaObject.invokeMethod(window, "openPane")
    assert split.property("paneExtent") == pytest.approx(400)
    assert split.property("contentOffset") == pytest.approx(400)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_split_view_pane_toggle_sits_after_the_visible_pane(split_scene):
    window, warnings, windows_before = split_scene
    split = _split(window)
    toggle = split.findChild(QQuickItem, "splitViewPaneToggle")
    assert toggle is not None
    assert toggle.isVisible()

    assert QMetaObject.invokeMethod(window, "useOverlay")
    assert toggle.x() == pytest.approx(4)
    assert QMetaObject.invokeMethod(window, "openPane")
    assert toggle.x() == pytest.approx(204)

    assert QMetaObject.invokeMethod(window, "closePane")
    assert QMetaObject.invokeMethod(window, "useCompactInline")
    assert toggle.x() == pytest.approx(52)
    assert QMetaObject.invokeMethod(window, "togglePane")
    assert split.property("paneOpen") is True
    assert toggle.x() == pytest.approx(204)

    toggle_area = split.findChild(QQuickItem, "splitViewPaneToggleArea")
    assert toggle_area is not None
    assert toggle_area.width() == pytest.approx(toggle.width())
    assert toggle.width() == pytest.approx(toggle.height())
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []
