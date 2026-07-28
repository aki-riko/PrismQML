# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Sliding-indicator invalid geometry regressions. 滑动指示器无效几何回归。"""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "sliding-indicator-invalid-geometry.qml")
)


def test_invalid_rectangles_are_ignored_without_numeric_assignment_warnings(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)

    source = b"""
import QtQuick
import "../../prismqml/PrismQML/controls/navigation/_internal"

Item {
    id: root
    property bool completed: false
    property real finalX: -1
    property real finalWidth: -1

    SlidingIndicatorAnimation {
        id: animation
        orientation: Qt.Horizontal
        mode: "stretch"
    }

    Component.onCompleted: {
        animation.setGeometry({ x: 10, y: 2, width: 40, height: 3 })
        animation.setGeometry({ x: undefined, y: 2, width: 40, height: 3 })
        animation.animateTo(
            { x: 10, y: 2, width: 40, height: 3 },
            { x: NaN, y: 2, width: 50, height: 3 })
        animation.animateTo(
            { x: 10, y: 2, width: 40, height: 3 },
            { x: 80, y: 2, width: Infinity, height: 3 })
        finalX = animation.indicatorX
        finalWidth = animation.indicatorWidth
        completed = true
    }
}
"""
    component = QQmlComponent(engine)
    component.setData(source, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    try:
        assert root is not None
        assert root.property("completed") is True
        assert root.property("finalX") == 10
        assert root.property("finalWidth") == 40
        assert not any(
            "Unable to assign" in warning or "Cannot assign" in warning
            for warning in warnings
        ), warnings
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
