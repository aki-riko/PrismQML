# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""FlowLayout cross-cell span contracts. FlowLayout 跨格合同。

Span semantics 跨格语义:
- default mode 默认模式: the cell is the item's own base extent, so columnSpan /
  rowSpan multiply that extent and the heightmap packs the larger footprint.
- vertical mode 垂直模式: columns are uniform, so columnSpan occupies whole
  columns and rowSpan multiplies the item's base height.
- horizontal mode 水平模式: rows are uniform, so rowSpan raises the row band by
  whole row units (no overlap with the following rows) and columnSpan widens the
  item and therefore changes where the row wraps.
"""

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

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
LAYOUT_DIR = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "containers" / "Layout"
)
SOURCE_PATHS = [
    LAYOUT_DIR / "FlowLayout.qml",
    LAYOUT_DIR / "FlowLayoutEngine.js",
]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "flow-layout-spans.qml")
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

    readonly property var spanReport: ({
        "dSpan": defaultFlow.spanOf(dSpan),
        "dPlain": defaultFlow.spanOf(dPlain),
        "cSpan": clampedFlow.spanOf(cSpan)
    })

    function dropColumnSpan() { dSpan.columnSpan = 1 }
    function restoreColumnSpan() { dSpan.columnSpan = 2 }

    FlowLayout {
        id: defaultFlow
        objectName: "defaultFlow"
        x: 10
        y: 10
        width: 300
        spacing: 10
        rowSpacing: 5

        Rectangle {
            id: dSpan
            objectName: "dSpan"
            property int columnSpan: 2
            width: 100
            height: 20
        }
        Rectangle { id: dPlain; objectName: "dPlain"; width: 60; height: 30 }
    }

    FlowLayout {
        id: verticalFlow
        objectName: "verticalFlow"
        x: 10
        y: 120
        width: 220
        mode: Enums.flow.vertical
        columnCount: 2
        spacing: 10
        rowSpacing: 5

        Rectangle { id: vA; objectName: "vA"; width: 100; height: 20 }
        Rectangle {
            id: vSpan
            objectName: "vSpan"
            property int columnSpan: 2
            width: 100
            height: 40
        }
        Rectangle {
            id: vRowSpan
            objectName: "vRowSpan"
            property int rowSpan: 2
            width: 100
            height: 20
        }
    }

    FlowLayout {
        id: horizontalFlow
        objectName: "horizontalFlow"
        x: 250
        y: 120
        width: 220
        mode: Enums.flow.horizontal
        spacing: 10
        rowSpacing: 5

        Rectangle { id: hA; objectName: "hA"; width: 100; height: 20 }
        Rectangle {
            id: hSpan
            objectName: "hSpan"
            property int columnSpan: 2
            width: 60
            height: 30
        }
        Rectangle {
            id: hRowSpan
            objectName: "hRowSpan"
            property int rowSpan: 2
            width: 50
            height: 20
        }
    }

    FlowLayout {
        id: clampedFlow
        objectName: "clampedFlow"
        x: 250
        y: 300
        width: 220
        mode: Enums.flow.vertical
        columnCount: 2
        spacing: 10
        rowSpacing: 5

        Rectangle {
            id: cSpan
            objectName: "cSpan"
            property int columnSpan: 5
            width: 100
            height: 30
        }
    }

    FlowLayout {
        id: explicitOneFlow
        objectName: "explicitOneFlow"
        x: 10
        y: 300
        width: 180
        spacing: 10
        rowSpacing: 5

        Rectangle {
            id: eA
            objectName: "eA"
            property int columnSpan: 1
            property int rowSpan: 1
            width: 100
            height: 20
        }
        Rectangle { id: eB; objectName: "eB"; width: 70; height: 40 }
        Rectangle { id: eC; objectName: "eC"; width: 60; height: 30 }
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
    assert _wait_for(
        lambda: window.findChild(QQuickItem, "defaultFlow")
        .property("implicitHeight") > 0
    )
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
def span_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        yield window, warnings, windows_before
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def _geometry(window, name):
    item = window.findChild(QQuickItem, name)
    assert item is not None
    return [item.x(), item.y(), item.width(), item.height()]


def _flow(window, name) -> QQuickItem:
    flow = window.findChild(QQuickItem, name)
    assert flow is not None
    return flow


def test_flow_layout_span_sources_follow_conventions():
    for source_path in SOURCE_PATHS:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        assert scan_source_text(source, path) == []


def test_flow_layout_default_mode_packs_the_span_footprint(span_scene):
    window, warnings, windows_before = span_scene
    flow = _flow(window, "defaultFlow")
    assert _geometry(window, "dSpan") == pytest.approx([0, 0, 210, 20])
    assert _geometry(window, "dPlain") == pytest.approx([220, 0, 60, 30])
    assert flow.property("implicitHeight") == pytest.approx(30)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_flow_layout_vertical_mode_spans_whole_columns(span_scene):
    window, warnings, windows_before = span_scene
    flow = _flow(window, "verticalFlow")
    assert _geometry(window, "vA") == pytest.approx([0, 0, 105, 20])
    assert _geometry(window, "vSpan") == pytest.approx([0, 25, 220, 40])
    assert _geometry(window, "vRowSpan") == pytest.approx([0, 70, 105, 45])
    assert flow.property("rowCount") == 2
    assert _variant(flow.property("rowHeights")) == pytest.approx([120, 70])
    assert flow.property("implicitHeight") == pytest.approx(115)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_flow_layout_horizontal_mode_spans_row_bands(span_scene):
    window, warnings, windows_before = span_scene
    flow = _flow(window, "horizontalFlow")
    assert _geometry(window, "hA") == pytest.approx([0, 0, 100, 20])
    assert _geometry(window, "hSpan") == pytest.approx([0, 25, 130, 65])
    assert _geometry(window, "hRowSpan") == pytest.approx([140, 25, 50, 65])
    assert flow.property("rowCount") == 2
    assert _variant(flow.property("rowHeights")) == pytest.approx([20, 65])
    assert flow.property("implicitHeight") == pytest.approx(90)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_flow_layout_clamps_spans_to_the_available_columns(span_scene):
    window, warnings, windows_before = span_scene
    flow = _flow(window, "clampedFlow")
    assert _geometry(window, "cSpan") == pytest.approx([0, 0, 220, 30])
    assert flow.property("implicitHeight") == pytest.approx(30)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_flow_layout_explicit_unit_spans_match_the_historical_geometry(span_scene):
    window, warnings, windows_before = span_scene
    flow = _flow(window, "explicitOneFlow")
    assert _geometry(window, "eA") == pytest.approx([0, 0, 100, 20])
    assert _geometry(window, "eB") == pytest.approx([110, 0, 70, 40])
    assert _geometry(window, "eC") == pytest.approx([0, 25, 60, 30])
    assert flow.property("implicitHeight") == pytest.approx(55)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_flow_layout_reports_normalized_spans(span_scene):
    window, warnings, windows_before = span_scene
    report = _variant(window.property("spanReport"))
    assert report["dSpan"] == {"rowSpan": 1, "columnSpan": 2}
    assert report["dPlain"] == {"rowSpan": 1, "columnSpan": 1}
    assert report["cSpan"] == {"rowSpan": 1, "columnSpan": 5}
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_flow_layout_relayouts_when_a_span_changes_at_runtime(span_scene):
    window, warnings, windows_before = span_scene
    assert _geometry(window, "dSpan") == pytest.approx([0, 0, 210, 20])
    assert QMetaObject.invokeMethod(window, "dropColumnSpan")
    assert _wait_for(
        lambda: _geometry(window, "dSpan") == pytest.approx([0, 0, 100, 20])
    )
    assert _geometry(window, "dPlain") == pytest.approx([110, 0, 60, 30])
    assert QMetaObject.invokeMethod(window, "restoreColumnSpan")
    assert _wait_for(
        lambda: _geometry(window, "dSpan") == pytest.approx([0, 0, 210, 20])
    )
    assert _geometry(window, "dPlain") == pytest.approx([220, 0, 60, 30])
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []
