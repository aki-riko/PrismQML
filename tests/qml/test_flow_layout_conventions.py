# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""FlowLayout geometry and public API contracts. FlowLayout 几何与公开 API 合同。"""

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

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "Layout"
    / "FlowLayout.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "flow-layout-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    readonly property real defaultHeight: defaultFlow.implicitHeight
    readonly property var defaultGeometry: [
        defaultA.x, defaultA.y, defaultA.width, defaultA.height,
        defaultB.x, defaultB.y, defaultB.width, defaultB.height,
        defaultC.x, defaultC.y, defaultC.width, defaultC.height
    ]
    readonly property int horizontalRowCount: horizontalFlow.rowCount
    readonly property var horizontalRowHeights: horizontalFlow.rowHeights
    readonly property real horizontalHeight: horizontalFlow.implicitHeight
    readonly property var horizontalGeometry: [
        horizontalA.x, horizontalA.y, horizontalA.width, horizontalA.height,
        horizontalB.x, horizontalB.y, horizontalB.width, horizontalB.height,
        horizontalC.x, horizontalC.y, horizontalC.width, horizontalC.height
    ]
    readonly property int fixedColumnCount: fixedVerticalFlow.rowCount
    readonly property var fixedColumnHeights: fixedVerticalFlow.rowHeights
    readonly property real fixedVerticalHeight: fixedVerticalFlow.implicitHeight
    readonly property var fixedVerticalGeometry: [
        fixedA.x, fixedA.y, fixedA.width, fixedA.height,
        fixedB.x, fixedB.y, fixedB.width, fixedB.height,
        fixedC.x, fixedC.y, fixedC.width, fixedC.height
    ]
    readonly property int autoColumnCount: autoVerticalFlow.rowCount
    readonly property var autoColumnHeights: autoVerticalFlow.rowHeights
    readonly property real autoVerticalHeight: autoVerticalFlow.implicitHeight
    readonly property var autoVerticalGeometry: [
        autoA.x, autoA.y, autoA.width, autoA.height,
        autoB.x, autoB.y, autoB.width, autoB.height,
        autoC.x, autoC.y, autoC.width, autoC.height
    ]
    readonly property int filteredRawCount: filteredFlow.count()
    readonly property int filteredVisibleCount:
        filteredFlow._getVisibleChildren().length
    readonly property bool filteredFirstExists: filteredFlow.itemAt(0) !== null
    readonly property int dynamicSpacing: dynamicFlow.spacing
    readonly property int dynamicRowSpacing: dynamicFlow.rowSpacing
    readonly property var dynamicMargins: [
        dynamicFlow.leftMargin, dynamicFlow.topMargin,
        dynamicFlow.rightMargin, dynamicFlow.bottomMargin
    ]

    property var dynamicItem: null
    property var insertedItem: null
    property int dynamicCount: -1
    property int dynamicIndex: -1
    property bool dynamicAtMatches: false
    property bool dynamicEmpty: true

    function enableHorizontalAspect() {
        horizontalFlow.preserveAspectRatio = true
    }

    function resizeAutoVerticalNarrow() {
        autoVerticalFlow.width = 230
    }

    function addDynamicItem() {
        dynamicItem = dynamicRectangle.createObject(
            root, {"objectName": "dynamicItem"}
        )
        dynamicFlow.addWidget(dynamicItem)
        captureDynamicState(dynamicItem)
    }

    function removeDynamicItem() {
        dynamicFlow.removeWidget(dynamicItem)
        captureDynamicState(null)
    }

    function insertDynamicItem() {
        insertedItem = dynamicRectangle.createObject(
            root, {"objectName": "insertedItem"}
        )
        dynamicFlow.insertWidget(0, insertedItem)
        captureDynamicState(insertedItem)
    }

    function configureDynamicFlow() {
        dynamicFlow.setSpacing(12)
        dynamicFlow.setContentsMargins(1, 2, 3, 4)
    }

    function clearDynamicFlow() {
        dynamicFlow.clear()
        captureDynamicState(null)
    }

    function captureDynamicState(candidate) {
        dynamicCount = dynamicFlow.count()
        dynamicIndex = candidate ? dynamicFlow.indexOf(candidate) : -1
        dynamicAtMatches = candidate
            && dynamicFlow.itemAt(dynamicIndex) === candidate
        dynamicEmpty = dynamicFlow.isEmpty()
    }

    width: 900
    height: 700

    FlowLayout {
        id: defaultFlow
        width: 180
        spacing: 10
        rowSpacing: 5

        Rectangle { id: defaultA; width: 100; height: 20 }
        Rectangle { id: defaultB; width: 70; height: 40 }
        Rectangle { id: defaultC; width: 60; height: 30 }
    }

    FlowLayout {
        id: horizontalFlow
        y: 100
        width: 180
        mode: Enums.flow.horizontal
        spacing: 10
        rowSpacing: 5

        Rectangle { id: horizontalA; width: 100; height: 20 }
        Rectangle { id: horizontalB; width: 70; height: 40 }
        Rectangle { id: horizontalC; width: 60; height: 30 }
    }

    FlowLayout {
        id: fixedVerticalFlow
        y: 200
        width: 220
        mode: Enums.flow.vertical
        spacing: 10
        rowSpacing: 5
        columnCount: 2

        Rectangle { id: fixedA; width: 100; height: 20 }
        Rectangle { id: fixedB; width: 70; height: 40 }
        Rectangle { id: fixedC; width: 60; height: 30 }
    }

    FlowLayout {
        id: autoVerticalFlow
        x: 300
        width: 350
        mode: Enums.flow.vertical
        spacing: 10
        rowSpacing: 5

        Rectangle { id: autoA; width: 100; height: 20 }
        Rectangle { id: autoB; width: 70; height: 40 }
        Rectangle { id: autoC; width: 60; height: 30 }
    }

    FlowLayout {
        id: filteredFlow
        x: 300
        y: 120
        width: 180
        spacing: 10
        rowSpacing: 5

        QtObject { objectName: "nonVisualObject" }
        Item { objectName: "zeroSizeItem"; width: 0; height: 0 }
        Repeater {
            model: 2
            Rectangle { objectName: "repeatedItem"; width: 40; height: 20 }
        }
        Rectangle { objectName: "directItem"; width: 50; height: 30 }
    }

    FlowLayout {
        id: dynamicFlow
        x: 300
        y: 240
        width: 200
        spacing: 10
        rowSpacing: 5

        Rectangle { objectName: "baseItem"; width: 60; height: 20 }
    }

    Component {
        id: dynamicRectangle
        Rectangle { width: 50; height: 25 }
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 800) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


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
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    assert _wait_for(lambda: root.property("horizontalRowCount") == 2)
    return engine, component, root, warnings


def _dispose_scene(engine, component, root) -> None:
    root.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def flow_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        yield root, warnings, windows_before
    finally:
        _dispose_scene(engine, component, root)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_flow_layout_modes_preserve_current_geometry(flow_scene):
    root, warnings, windows_before = flow_scene
    assert _variant(root.property("defaultGeometry")) == pytest.approx(
        [0, 0, 100, 20, 110, 0, 70, 40, 0, 25, 60, 30]
    )
    assert root.property("defaultHeight") == pytest.approx(55)

    assert _variant(root.property("horizontalGeometry")) == pytest.approx(
        [0, 0, 100, 40, 110, 0, 70, 40, 0, 45, 60, 30]
    )
    assert root.property("horizontalRowCount") == 2
    assert _variant(root.property("horizontalRowHeights")) == [40, 30]
    assert root.property("horizontalHeight") == pytest.approx(75)

    assert _variant(root.property("fixedVerticalGeometry")) == pytest.approx(
        [0, 0, 105, 20, 115, 0, 105, 40, 0, 25, 105, 30]
    )
    assert root.property("fixedColumnCount") == 2
    assert _variant(root.property("fixedColumnHeights")) == pytest.approx(
        [60, 45]
    )
    assert root.property("fixedVerticalHeight") == pytest.approx(55)
    assert warnings == []
    assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_flow_layout_aspect_ratio_and_width_relayout(flow_scene):
    root, warnings, windows_before = flow_scene
    assert QMetaObject.invokeMethod(root, "enableHorizontalAspect")
    assert _wait_for(
        lambda: _variant(root.property("horizontalGeometry"))[2]
        == pytest.approx(200)
    )
    assert _variant(root.property("horizontalGeometry")) == pytest.approx(
        [0, 0, 200, 40, 210, 0, 70, 40, 0, 45, 60, 30]
    )

    assert root.property("autoColumnCount") == 3
    assert _variant(root.property("autoColumnHeights")) == pytest.approx(
        [25, 45, 35]
    )
    assert root.property("autoVerticalHeight") == pytest.approx(40)
    assert QMetaObject.invokeMethod(root, "resizeAutoVerticalNarrow")
    assert _wait_for(lambda: root.property("autoColumnCount") == 2)
    assert _variant(root.property("autoVerticalGeometry")) == pytest.approx(
        [0, 0, 110, 20, 120, 0, 110, 40, 0, 25, 110, 30]
    )
    assert _variant(root.property("autoColumnHeights")) == pytest.approx(
        [60, 45]
    )
    assert root.property("autoVerticalHeight") == pytest.approx(55)
    assert warnings == []
    assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_flow_layout_public_methods_and_child_filtering(flow_scene):
    root, warnings, windows_before = flow_scene
    assert root.property("filteredVisibleCount") == 3
    assert root.property("filteredRawCount") > root.property("filteredVisibleCount")
    assert root.property("filteredFirstExists")

    assert QMetaObject.invokeMethod(root, "addDynamicItem")
    assert root.property("dynamicCount") == 2
    assert root.property("dynamicIndex") == 1
    assert root.property("dynamicAtMatches")
    assert not root.property("dynamicEmpty")

    assert QMetaObject.invokeMethod(root, "configureDynamicFlow")
    assert root.property("dynamicSpacing") == 12
    assert root.property("dynamicRowSpacing") == 12
    assert _variant(root.property("dynamicMargins")) == [1, 2, 3, 4]
    assert QMetaObject.invokeMethod(root, "removeDynamicItem")
    assert root.property("dynamicCount") == 1
    assert not root.property("dynamicEmpty")

    assert QMetaObject.invokeMethod(root, "insertDynamicItem")
    assert root.property("dynamicCount") == 2
    assert root.property("dynamicIndex") >= 0
    assert root.property("dynamicAtMatches")

    assert QMetaObject.invokeMethod(root, "clearDynamicFlow")
    assert root.property("dynamicCount") == 0
    assert root.property("dynamicEmpty")
    assert warnings == []
    assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_flow_layout_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
