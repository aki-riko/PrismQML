# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Public ScrollArea runtime contracts. 公开 ScrollArea 运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import Skin, getSkin, register_types, setSkin
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "containers" / "ScrollArea.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "scroll-area-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property int defaultType: Enums.scroll.type_default
    readonly property int listType: Enums.scroll.type_list
    readonly property int gridType: Enums.scroll.type_grid
    readonly property int areaType: area.type
    readonly property real areaY: area.contentY
    readonly property real areaOriginY: area.flickableItem ? area.flickableItem.originY : 0
    readonly property real areaContentHeight: area.contentHeight
    readonly property int areaCount: area.count
    readonly property real areaImplicitWidth: area.implicitWidth
    readonly property real areaImplicitHeight: area.implicitHeight

    function scrollDefault() { area.smoothScrollTo(120) }
    function showList() {
        area.type = Enums.scroll.type_list
        area.currentIndex = 4
    }
    function scrollList() { area.scrollToIndex(10) }
    function showGrid() {
        area.setCellSize(55, 35)
        area.type = Enums.scroll.type_grid
        area.currentIndex = 6
    }
    function scrollBottom() { area.scrollToBottom() }
    function scrollTop() { area.scrollToTop() }
    function showDefault() { area.type = Enums.scroll.type_default }

    width: 640
    height: 360
    visible: true

    Component {
        id: itemDelegate
        Rectangle {
            width: ListView.view ? ListView.view.width : 55
            height: 30
        }
    }

    ScrollArea {
        id: area
        objectName: "scrollArea"
        x: 20
        y: 20
        width: 220
        height: 140
        preferredWidth: 240
        preferredHeight: 180
        model: 20
        delegate: itemDelegate
        itemHeight: 30

        Rectangle {
            objectName: "defaultContent"
            width: 360
            height: 420
        }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


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
    area = window.findChild(QQuickItem, "scrollArea")
    assert area is not None
    _pump()
    return engine, component, window, area, warnings


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
def scroll_area_scene(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_scroll_area_default_content_size_and_scroll(scroll_area_scene):
    window, _area, warnings, windows_before = scroll_area_scene
    assert window.property("areaType") == window.property("defaultType")
    assert window.property("areaImplicitWidth") == pytest.approx(240)
    assert window.property("areaImplicitHeight") == pytest.approx(180)
    assert _wait_for(lambda: window.property("areaContentHeight") == pytest.approx(452))

    assert QMetaObject.invokeMethod(window, "scrollDefault")
    assert _wait_for(lambda: window.property("areaY") == pytest.approx(120))
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_scroll_area_switches_list_grid_and_back(scroll_area_scene):
    window, area, warnings, windows_before = scroll_area_scene
    indices = []
    area.indexChanged.connect(indices.append)

    assert QMetaObject.invokeMethod(window, "showList")
    assert _wait_for(lambda: window.property("areaType") == window.property("listType"))
    assert _wait_for(lambda: window.property("areaCount") == 20)
    assert _wait_for(lambda: indices and indices[-1] == 4)
    assert QMetaObject.invokeMethod(window, "scrollList")
    assert _wait_for(lambda: window.property("areaY") == pytest.approx(300))

    assert QMetaObject.invokeMethod(window, "showGrid")
    assert _wait_for(lambda: window.property("areaType") == window.property("gridType"))
    assert _wait_for(lambda: window.property("areaCount") == 20)
    assert _wait_for(lambda: indices and indices[-1] == 6)
    assert QMetaObject.invokeMethod(window, "scrollBottom")
    assert _wait_for(
        lambda: window.property("areaY")
        == pytest.approx(
            window.property("areaOriginY")
            + window.property("areaContentHeight")
            - area.height()
        )
    )
    assert QMetaObject.invokeMethod(window, "scrollTop")
    assert _wait_for(lambda: window.property("areaY") == pytest.approx(0))

    assert QMetaObject.invokeMethod(window, "showDefault")
    assert _wait_for(lambda: window.property("areaType") == window.property("defaultType"))
    assert _wait_for(lambda: window.property("areaContentHeight") == pytest.approx(452))
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_scroll_area_source_follows_conventions():
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(SOURCE_PATH.read_text(encoding="utf-8"), path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []


def test_default_scroll_area_does_not_toggle_pixel_alignment_by_skin(qapp):
    previous_skin = getSkin()
    setSkin(Skin.FLUENT)
    engine, component, window, area, warnings = _create_scene()
    try:
        viewport = area.property("flickableItem")
        assert viewport is not None
        for skin in (Skin.FLUENT, Skin.NEOBRUTALISM, Skin.VINTAGE_TICKET):
            setSkin(skin)
            _pump()
            assert viewport.property("pixelAligned") is False
        assert warnings == []
    finally:
        setSkin(previous_skin)
        _dispose_scene(engine, component, window)
