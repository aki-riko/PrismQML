# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Color circle geometry and convention regressions. 圆形颜色选择器几何与规范回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "color-circles.qml"))
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    width: 400
    height: 100

    ColorPicker {
        id: picker
        objectName: "picker"
        type: Enums.colorPicker.type_circle
        selectedColor: circleColors[0]
    }
}
"""


def _descendants(root: QObject) -> list[QObject]:
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _create_scene(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert not component.isError(), [error.toString() for error in component.errors()]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    qapp.processEvents()
    return engine, component, root, warnings


def _circle_control(picker: QObject) -> QQuickItem:
    matches = [
        child
        for child in _descendants(picker)
        if child.metaObject().indexOfProperty("circleSize") >= 0
        and child.metaObject().indexOfProperty("colors") >= 0
    ]
    assert len(matches) == 1
    assert isinstance(matches[0], QQuickItem)
    return matches[0]


def _selected_delegate(circles: QQuickItem) -> QQuickItem:
    candidates = [
        child
        for child in _visual_descendants(circles)
        if child.metaObject().indexOfProperty("selected") >= 0
    ]
    matches = [child for child in candidates if child.property("selected")]
    assert len(matches) == 1, [
        (child.metaObject().className(), child.property("selected"))
        for child in candidates
    ]
    assert isinstance(matches[0], QQuickItem)
    return matches[0]


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def test_public_color_circles_preserve_runtime_geometry(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene(qapp)
    try:
        picker = root.findChild(QObject, "picker")
        assert picker is not None
        circles = _circle_control(picker)
        assert circles.property("circleSize") == 28
        assert circles.property("implicitHeight") == pytest.approx(36)

        selected = _selected_delegate(circles)
        assert selected.width() == pytest.approx(36)
        assert selected.height() == pytest.approx(36)
        sizes = sorted(
            (child.width(), child.height(), child.opacity())
            for child in selected.childItems()
        )
        assert (28.0, 28.0, 1.0) in sizes
        assert (34.0, 34.0, 0.6) in sizes
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()
