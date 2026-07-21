# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Dropdown indicator geometry regressions. 下拉指示箭头几何回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types

ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "button-dropdown-indicator.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    readonly property int expectedIndicatorWidth: Enums.controlSize.dropdownArrowWidth
    readonly property int expectedToolButtonWidth: Enums.controlSize.buttonHeight

    width: 180
    height: 80

    Button {
        id: defaultIndicatorButton
        objectName: "defaultIndicatorButton"
        width: contentWidth
        height: contentHeight
        icon: Enums.icon.more_horizontal
        feature: Enums.button.feature_dropdown
        menuItems: ["Alpha"]
    }

    Button {
        id: hiddenIndicatorButton
        objectName: "hiddenIndicatorButton"
        y: 40
        width: 38
        height: 28
        icon: Enums.icon.more_horizontal
        feature: Enums.button.feature_dropdown
        showDropdownIndicator: false
        menuItems: ["Alpha"]
    }
}
"""


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
    assert warnings == []
    return engine, component, root


def _descendants(root):
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _button(root, name):
    button = root.findChild(QObject, name)
    assert button is not None
    return button


def _chevrons(button):
    return [
        child
        for child in _descendants(button)
        if isinstance(child, QQuickItem)
        and child.isVisible()
        and "ChevronIcon" in child.metaObject().className()
    ]


def _content_icon(button):
    matches = [
        child
        for child in _descendants(button)
        if isinstance(child, QQuickItem)
        and child.metaObject().className().startswith("Icon_QMLTYPE_")
        and child.metaObject().indexOfProperty("icon") >= 0
        and child.property("icon") == button.property("icon")
    ]
    assert len(matches) == 1, [child.metaObject().className() for child in matches]
    return matches[0]


@pytest.fixture
def dropdown_indicator_scene(qapp):
    engine, component, root = _create_scene()
    try:
        yield root
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()


def test_icon_dropdown_default_width_keeps_indicator_clear_of_icon(
    dropdown_indicator_scene,
):
    root = dropdown_indicator_scene
    button = _button(root, "defaultIndicatorButton")
    icon = _content_icon(button)
    chevrons = _chevrons(button)

    assert button.property("showDropdownIndicator") is True
    assert button.property("contentWidth") == pytest.approx(
        root.property("expectedToolButtonWidth")
        + root.property("expectedIndicatorWidth")
    )
    assert len(chevrons) == 1
    icon_left = icon.mapToItem(button, QPointF()).x()
    chevron_left = chevrons[0].mapToItem(button, QPointF()).x()
    assert chevron_left >= icon_left + icon.width()


def test_icon_dropdown_can_hide_indicator_and_center_icon(dropdown_indicator_scene):
    root = dropdown_indicator_scene
    button = _button(root, "hiddenIndicatorButton")
    icon = _content_icon(button)

    assert button.property("showDropdownIndicator") is False
    assert button.property("contentWidth") == pytest.approx(
        root.property("expectedToolButtonWidth")
    )
    assert _chevrons(button) == []
    icon_left = icon.mapToItem(button, QPointF()).x()
    assert icon_left + icon.width() / 2 == pytest.approx(button.width() / 2)
