# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ParallaxView scroll driven offset contracts. ParallaxView 滚动视差位移合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    Q_ARG,
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

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
LAYOUT_DIR = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "containers" / "Layout"
)
SOURCE_PATHS = [
    LAYOUT_DIR / "ParallaxView.qml",
    LAYOUT_DIR / "_internal" / "ParallaxViewContent.qml",
]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "parallax-view-scroll.qml")
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

    function setSourceY(value) { source.contentY = value }
    function setSourceX(value) { source.contentX = value }
    function setScrollAreaY(value) {
        scrollArea.flickableItem.contentY = value
    }

    Flickable {
        id: source
        objectName: "source"
        x: 10
        y: 10
        width: 200
        height: 100
        contentWidth: 400
        contentHeight: 400

        Rectangle { width: 400; height: 400 }
    }

    ParallaxView {
        id: rangedParallax
        objectName: "rangedParallax"
        x: 220
        y: 10
        width: 200
        height: 100
        source: source
        horizontalShift: 40
        verticalShift: 100
        horizontalSourceStartOffset: 0
        horizontalSourceEndOffset: 400
        verticalSourceStartOffset: 50
        verticalSourceEndOffset: 250

        Rectangle { objectName: "rangedBackground"; anchors.fill: parent }
    }

    ParallaxView {
        id: autoParallax
        objectName: "autoParallax"
        x: 430
        y: 10
        width: 200
        height: 100
        source: source
        verticalShift: 100

        Rectangle { objectName: "autoBackground"; anchors.fill: parent }
    }

    ParallaxView {
        id: detachedParallax
        objectName: "detachedParallax"
        x: 10
        y: 130
        width: 200
        height: 100
        verticalShift: 100

        Rectangle { objectName: "detachedBackground"; anchors.fill: parent }
    }

    ScrollArea {
        id: scrollArea
        objectName: "scrollArea"
        x: 220
        y: 130
        width: 200
        height: 100
        padding: 0

        Rectangle { width: 200; height: 500 }
    }

    ParallaxView {
        id: scrollParallax
        objectName: "scrollParallax"
        x: 430
        y: 130
        width: 200
        height: 100
        source: scrollArea
        verticalShift: 60

        Rectangle { objectName: "scrollBackground"; anchors.fill: parent }
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
def parallax_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        yield window, warnings, windows_before
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def _parallax(window, name) -> QQuickItem:
    item = window.findChild(QQuickItem, name)
    assert item is not None
    return item


def test_parallax_view_sources_follow_conventions():
    for source_path in SOURCE_PATHS:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        assert scan_source_text(source, path) == []


def test_parallax_view_keeps_the_visual_tree_in_internal():
    entry = SOURCE_PATHS[0].read_text(encoding="utf-8")
    content = SOURCE_PATHS[1].read_text(encoding="utf-8")
    assert len(entry.splitlines()) < 300
    assert "required property Item host" in content
    assert "required property Item host" not in entry
    for marker in ("Rectangle {", "MouseArea {"):
        assert marker not in entry


def test_parallax_view_uses_the_declared_source_range(parallax_scene):
    window, warnings, windows_before = parallax_scene
    parallax = _parallax(window, "rangedParallax")
    background = parallax.findChild(QQuickItem, "parallaxBackgroundHost")
    assert background is not None

    assert parallax.property("verticalProgress") == pytest.approx(0)
    assert parallax.property("verticalOffset") == pytest.approx(0)

    assert QMetaObject.invokeMethod(window, "setSourceY", Q_ARG("QVariant", 50))
    assert _wait_for(
        lambda: parallax.property("verticalProgress") == pytest.approx(0)
    )
    assert parallax.property("verticalOffset") == pytest.approx(0)

    assert QMetaObject.invokeMethod(window, "setSourceY", Q_ARG("QVariant", 150))
    assert _wait_for(
        lambda: parallax.property("verticalProgress") == pytest.approx(0.5)
    )
    assert parallax.property("verticalOffset") == pytest.approx(-50)
    assert background.y() == pytest.approx(-50)

    assert QMetaObject.invokeMethod(window, "setSourceY", Q_ARG("QVariant", 250))
    assert _wait_for(
        lambda: parallax.property("verticalProgress") == pytest.approx(1)
    )
    assert parallax.property("verticalOffset") == pytest.approx(-100)

    assert QMetaObject.invokeMethod(window, "setSourceY", Q_ARG("QVariant", 380))
    assert parallax.property("verticalProgress") == pytest.approx(1)
    assert parallax.property("verticalOffset") == pytest.approx(-100)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_parallax_view_horizontal_axis(parallax_scene):
    window, warnings, windows_before = parallax_scene
    parallax = _parallax(window, "rangedParallax")
    background = parallax.findChild(QQuickItem, "parallaxBackgroundHost")
    assert background is not None

    assert QMetaObject.invokeMethod(window, "setSourceX", Q_ARG("QVariant", 200))
    assert _wait_for(
        lambda: parallax.property("horizontalProgress") == pytest.approx(0.5)
    )
    assert parallax.property("horizontalOffset") == pytest.approx(-20)
    assert background.x() == pytest.approx(-20)
    assert parallax.property("verticalProgress") == pytest.approx(0)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_parallax_view_derives_the_range_from_the_source(parallax_scene):
    window, warnings, windows_before = parallax_scene
    parallax = _parallax(window, "autoParallax")

    assert QMetaObject.invokeMethod(window, "setSourceY", Q_ARG("QVariant", 150))
    assert _wait_for(
        lambda: parallax.property("verticalProgress") == pytest.approx(0.5)
    )
    assert parallax.property("verticalOffset") == pytest.approx(-50)

    assert QMetaObject.invokeMethod(window, "setSourceY", Q_ARG("QVariant", 300))
    assert _wait_for(
        lambda: parallax.property("verticalProgress") == pytest.approx(1)
    )
    assert parallax.property("verticalOffset") == pytest.approx(-100)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_parallax_view_without_a_source_stays_still(parallax_scene):
    window, warnings, windows_before = parallax_scene
    parallax = _parallax(window, "detachedParallax")
    assert parallax.property("source") is None
    assert parallax.property("verticalProgress") == pytest.approx(0)
    assert parallax.property("verticalOffset") == pytest.approx(0)
    assert QMetaObject.invokeMethod(window, "setSourceY", Q_ARG("QVariant", 200))
    _pump()
    assert parallax.property("verticalOffset") == pytest.approx(0)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_parallax_view_tracks_a_scroll_area_source(parallax_scene):
    window, warnings, windows_before = parallax_scene
    scroll_area = window.findChild(QQuickItem, "scrollArea")
    parallax = _parallax(window, "scrollParallax")
    assert scroll_area is not None
    assert parallax.property("source") is scroll_area
    assert scroll_area.property("contentHeight") == pytest.approx(500)

    assert QMetaObject.invokeMethod(window, "setScrollAreaY", Q_ARG("QVariant", 200))
    assert _wait_for(
        lambda: parallax.property("verticalProgress") == pytest.approx(0.5)
    )
    assert parallax.property("verticalOffset") == pytest.approx(-30)

    assert QMetaObject.invokeMethod(window, "setScrollAreaY", Q_ARG("QVariant", 400))
    assert _wait_for(
        lambda: parallax.property("verticalProgress") == pytest.approx(1)
    )
    assert parallax.property("verticalOffset") == pytest.approx(-60)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []
