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
    readonly property int expectedContentPadding: Enums.spacing.m
    readonly property real expectedDropdownArrowMargin: Enums.spacing.m
    readonly property real expectedSplitArrowInset:
        Enums.spacing.micro + Enums.spacing.xxxl / 2
    readonly property int featureDropdown: Enums.button.feature_dropdown
    readonly property int featureSplit: Enums.button.feature_split

    width: 180
    height: 120

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

    Button {
        id: dynamicIndicatorButton
        objectName: "dynamicIndicatorButton"
        y: 80
        width: 180
        height: 40
        text: "Dynamic"
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


def _all_chevrons(button):
    return [
        child
        for child in _descendants(button)
        if isinstance(child, QQuickItem)
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


def _content_text(button, text):
    matches = [
        child
        for child in _descendants(button)
        if isinstance(child, QQuickItem)
        and child.metaObject().indexOfProperty("paintedWidth") >= 0
        and child.metaObject().indexOfProperty("text") >= 0
        and child.property("text") == text
    ]
    assert len(matches) == 1, [child.metaObject().className() for child in matches]
    return matches[0]


def _center_x(item, relative_to):
    return item.mapToItem(relative_to, QPointF()).x() + item.width() / 2


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


def test_dropdown_reuses_one_arrow_and_preserves_external_open_state(
    dropdown_indicator_scene,
):
    root = dropdown_indicator_scene
    default_button = _button(root, "defaultIndicatorButton")
    hidden_button = _button(root, "hiddenIndicatorButton")
    default_arrows = _all_chevrons(default_button)

    assert len(default_arrows) == 1
    assert len(_all_chevrons(hidden_button)) == 1
    assert not default_arrows[0].property("isOpen")
    assert _center_x(default_arrows[0], default_button) == pytest.approx(
        default_button.width()
        - root.property("expectedDropdownArrowMargin")
        - default_arrows[0].width() / 2
    )

    default_button.setProperty("dropdownOpen", True)
    assert default_arrows[0].property("isOpen")

    default_button.setProperty("dropdownOpen", False)
    assert not default_arrows[0].property("isOpen")

    hidden_button.setProperty("showDropdownIndicator", True)
    assert len(_chevrons(hidden_button)) == 1
    hidden_button.setProperty("showDropdownIndicator", False)
    assert _chevrons(hidden_button) == []

    default_button.setProperty("feature", root.property("featureSplit"))
    default_button.setProperty("dropdownOpen", True)
    assert not default_arrows[0].property("isOpen")
    assert _center_x(default_arrows[0], default_button) == pytest.approx(
        default_button.width() - root.property("expectedSplitArrowInset")
    )

    default_button.setProperty("feature", root.property("featureDropdown"))
    assert default_arrows[0].property("isOpen")
    assert _center_x(default_arrows[0], default_button) == pytest.approx(
        default_button.width()
        - root.property("expectedDropdownArrowMargin")
        - default_arrows[0].width() / 2
    )


def test_text_dropdown_restores_content_geometry_after_indicator_toggle(
    dropdown_indicator_scene,
):
    root = dropdown_indicator_scene
    button = _button(root, "dynamicIndicatorButton")
    text = _content_text(button, "Dynamic")

    button.setProperty("showDropdownIndicator", True)
    button.setProperty("showDropdownIndicator", False)

    restored_content_width = button.property("contentWidth")
    restored_text_x = text.mapToItem(button, QPointF()).x()
    assert button.property("contentWidth") == pytest.approx(button.width())
    assert restored_text_x == pytest.approx(root.property("expectedContentPadding"))

    resize_delta = root.property("expectedIndicatorWidth")
    button.setProperty("width", button.width() + resize_delta)

    assert button.property("contentWidth") == pytest.approx(restored_content_width)
    assert text.mapToItem(button, QPointF()).x() == pytest.approx(
        restored_text_x + resize_delta / 2
    )
