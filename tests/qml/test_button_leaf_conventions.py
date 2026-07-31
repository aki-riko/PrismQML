# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Button leaf convention regressions. 按钮叶组件规范回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
BUTTON_SOURCES = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "buttons" / "CloseButton.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "buttons"
    / "InputActionButton.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "buttons"
    / "Button"
    / "ButtonProgress.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "buttons"
    / "Button"
    / "ButtonContent.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "buttons"
    / "Button"
    / "ButtonDropdown.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "buttons"
    / "Button"
    / "CustomButtonCore.qml",
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "button-leaf-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/buttons" as Buttons
import "../../prismqml/PrismQML/controls/buttons/Button" as ButtonParts

Item {
    property var dropdownLongMenuItems: [
        "One", "Two", "Three", "Four", "Five",
        "Six", "Seven", "Eight", "Nine", "Ten"
    ]

    readonly property real closeWidth: closeButton.width
    readonly property real closeHeight: closeButton.height
    readonly property bool closeHovered: closeButton.hovered
    readonly property bool closePressed: closeButton.pressed
    readonly property real actionWidth: actionButton.preferredWidth
    readonly property real actionHeight: actionButton.preferredHeight
    readonly property int actionStyle: actionButton.style
    readonly property int actionShape: actionButton.shape
    readonly property int transparentStyle: Enums.button.style_transparent
    readonly property int defaultShape: Enums.button.shape_default
    readonly property real progressWidth: progressFeature.width
    readonly property real progressHeight: progressFeature.height
    readonly property int progressFeatureType: progressFeature.feature
    readonly property real progressValue: progressFeature.progress
    readonly property bool progressVisible: progressFeature.showProgress
    readonly property int expectedProgressFeature: Enums.button.feature_progress_bar
    readonly property int expectedIndeterminateRingFeature:
        Enums.button.feature_indeterminate_ring
    readonly property color expectedRingTrackLight: Enums.stateColor.track
    readonly property color expectedRingTrackDark: Enums.stateColor.whiteOverlay
    readonly property color expectedButtonTextColor: contentButton.getTextColor()
    readonly property int expectedDropdownFeature: Enums.button.feature_dropdown
    readonly property int expectedSplitFeature: Enums.button.feature_split
    readonly property int expectedDefaultStyle: Enums.button.style_default
    readonly property int expectedSmallContentHeight:
        Enums.comboBoxMetrics.itemHeight * 2
        + Enums.controlSize.menuSeparatorHeight
    readonly property int expectedSmallPopupHeight: Enums.comboBoxMetrics.popupPadding
                                                    + expectedSmallContentHeight
    readonly property int expectedPopupMaxHeight: Enums.comboBoxMetrics.popupMaxHeight
    readonly property int expectedSmallRadius: Enums.radius.small
    readonly property color expectedDropdownTextColor: dropdownButton.getTextColor()
    readonly property int expectedScreenPickerType: Enums.colorPicker.type_screen
    readonly property int expectedButtonMinWidth: Enums.controlSize.buttonMinWidth
    readonly property int expectedInputHeight: Enums.controlSize.inputHeight

    width: 400
    height: 200

    Buttons.CloseButton {
        id: closeButton
    }

    Item {
        width: 100
        height: 40

        Buttons.InputActionButton {
            id: actionButton
        }
    }

    Item {
        width: 200
        height: 10

        ButtonParts.ButtonProgress {
            id: progressFeature
            feature: Enums.button.feature_progress_bar
            style: Enums.button.style_primary
            progress: 0.4
            showProgress: true
            parentRadius: Enums.radius.small
        }
    }

    Button {
        id: contentButton
        objectName: "contentButton"
        width: 180
        height: 40
        feature: Enums.button.feature_progress_ring
        style: Enums.button.style_primary
        text: "Ready"
        icon: Enums.icon.checkmark
        iconSize: 18
        loadingText: "Working"
        progress: 0.25
        fontBold: true
        fontItalic: true
        fontUnderline: true
        fontStrikeout: true
        countdownText: " sec"
    }

    Button {
        id: dropdownButton
        objectName: "dropdownButton"
        y: 80
        width: 180
        height: 40
        feature: Enums.button.feature_dropdown
        style: Enums.button.style_primary
        text: "Menu"
        icon: Enums.icon.checkmark
        radius: Enums.radius.large
        menuItems: ["Alpha", "-", { text: "Beta", icon: Enums.icon.checkmark }]
    }

    ColorPicker {
        id: screenPicker
        objectName: "screenPicker"
        y: 140
        width: 200
        height: 40
        type: Enums.colorPicker.type_screen
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    qml_warnings = []
    engine.warnings.connect(
        lambda errors: qml_warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump(20)
    assert qml_warnings == []
    return engine, component, root


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def _descendants(root):
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _button_content(button):
    matches = [
        child
        for child in _descendants(button)
        if child.metaObject().indexOfProperty("_ringBorderColor") >= 0
        and child.metaObject().indexOfProperty("countdownRemaining") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _progress_rings(content):
    return [
        child
        for child in _descendants(content)
        if child.metaObject().className().startswith("ProgressRing_QMLTYPE_")
    ]


def _button_dropdown(button):
    matches = [
        child
        for child in _descendants(button)
        if child.metaObject().indexOfProperty("isMenuOpen") >= 0
        and child.metaObject().indexOfProperty("mainHovered") >= 0
        and child.metaObject().indexOfProperty("dropHovered") >= 0
        and child.metaObject().indexOfProperty("parentStyle") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _dropdown_popup(dropdown):
    matches = [
        child
        for child in _descendants(dropdown)
        if child.metaObject().indexOfProperty("_itemsHeight") >= 0
        and child.metaObject().indexOfProperty("_needsScroll") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _custom_button_core(picker):
    matches = [
        child
        for child in _descendants(picker)
        if child.metaObject().indexOfProperty("buttonState") >= 0
        and child.metaObject().indexOfProperty("contentOffsetX") >= 0
        and child.metaObject().indexOfProperty("radius_") >= 0
        and child.metaObject().indexOfProperty("getBackgroundColor") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _assert_dropdown_parent_bindings(button, dropdown):
    property_pairs = (
        ("isToolButton", "isToolButton"),
        ("feature", "feature"),
        ("menuItems", "menuItems"),
        ("enabled", "controlEnabled"),
        ("loading", "loading"),
        ("radius", "parentRadius"),
        ("fontSize", "fontSize"),
        ("style", "parentStyle"),
    )
    for parent_name, child_name in property_pairs:
        parent_value = button.property(parent_name)
        child_value = dropdown.property(child_name)
        if parent_name == "menuItems":
            parent_value = parent_value.toVariant()
            child_value = child_value.toVariant()
        assert child_value == parent_value


def _assert_dropdown_idle(dropdown):
    for name in ("isMenuOpen", "mainHovered", "mainPressed",
                 "dropHovered", "dropPressed"):
        assert not dropdown.property(name)


def _set_long_split_state(root, button):
    button.setProperty("feature", root.property("expectedSplitFeature"))
    button.setProperty("text", "")
    button.setProperty("enabled", False)
    button.setProperty("loading", True)
    button.setProperty("style", root.property("expectedDefaultStyle"))
    button.setProperty("radius", root.property("expectedSmallRadius"))
    button.setProperty("menuItems", root.property("dropdownLongMenuItems"))


@pytest.fixture
def button_leaf_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root = _create_scene()
    try:
        yield root, windows_before
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_button_leaf_runtime_defaults_remain_stable(button_leaf_scene):
    root, windows_before = button_leaf_scene
    assert (root.property("closeWidth"), root.property("closeHeight")) == (28, 28)
    assert not root.property("closeHovered")
    assert not root.property("closePressed")
    assert (root.property("actionWidth"), root.property("actionHeight")) == (30, 30)
    assert root.property("actionStyle") == root.property("transparentStyle")
    assert root.property("actionShape") == root.property("defaultShape")
    assert (root.property("progressWidth"), root.property("progressHeight")) == (
        200,
        3,
    )
    assert root.property("progressFeatureType") == root.property(
        "expectedProgressFeature"
    )
    assert root.property("progressValue") == pytest.approx(0.4)
    assert root.property("progressVisible")
    assert _new_visible_windows(windows_before) == []


def test_button_content_parent_bindings_remain_stable(button_leaf_scene):
    root, windows_before = button_leaf_scene
    button = root.findChild(QObject, "contentButton")
    assert button is not None
    content = _button_content(button)
    for name in ("feature", "style", "text", "icon", "iconSize", "loading",
                 "loadingText", "progress", "fontBold", "fontItalic",
                 "fontUnderline", "fontStrikeout", "countdownText"):
        assert content.property(name) == button.property(name)
    assert content.property("textColor") == root.property("expectedButtonTextColor")
    assert content.property("controlEnabled") == button.property("enabled")
    assert content.property("fontSize") == button.property("fontSize")
    assert content.property("pressed") == button.property("pressed")
    assert not content.property("countdownActive")
    assert content.property("countdownRemaining") == 0

    button.setProperty("text", "Updated")
    button.setProperty("progress", 0.75)
    button.setProperty("loading", True)
    button.setProperty("pseudoPressed", True)
    button.setProperty("enabled", False)
    _pump(20)
    assert content.property("text") == "Updated"
    assert content.property("progress") == pytest.approx(0.75)
    assert content.property("loading")
    assert content.property("pressed")
    assert not content.property("controlEnabled")
    assert content.property("textColor") == root.property("expectedButtonTextColor")
    assert _new_visible_windows(windows_before) == []


def test_button_content_reuses_one_feature_ring_loader(button_leaf_scene):
    root, windows_before = button_leaf_scene
    button = root.findChild(QObject, "contentButton")
    assert button is not None
    content = _button_content(button)

    rings = _progress_rings(content)
    assert len(rings) == 1
    assert not rings[0].property("indeterminate")
    assert rings[0].property("value") == pytest.approx(0.25)
    assert rings[0].property("trackColorLight") == content.property(
        "_ringBorderColor"
    )
    assert rings[0].property("trackColorDark") == content.property(
        "_ringBorderColor"
    )

    button.setProperty("feature", root.property("expectedIndeterminateRingFeature"))
    _pump(20)
    rings = _progress_rings(content)
    assert len(rings) == 1
    assert rings[0].property("indeterminate")
    assert rings[0].property("trackColorLight") == root.property(
        "expectedRingTrackLight"
    )
    assert rings[0].property("trackColorDark") == root.property(
        "expectedRingTrackDark"
    )

    button.setProperty("loading", True)
    _pump(20)
    assert len(_progress_rings(content)) == 2
    assert _new_visible_windows(windows_before) == []


def test_button_dropdown_parent_bindings_remain_stable(button_leaf_scene):
    root, windows_before = button_leaf_scene
    button = root.findChild(QObject, "dropdownButton")
    assert button is not None
    dropdown = _button_dropdown(button)
    popup = _dropdown_popup(dropdown)
    _assert_dropdown_parent_bindings(button, dropdown)
    _assert_dropdown_idle(dropdown)
    assert dropdown.property("textColor") == root.property("expectedDropdownTextColor")
    assert popup.property("_itemsHeight") == root.property("expectedSmallContentHeight")
    assert popup.property("popupHeight") == root.property("expectedSmallPopupHeight")
    assert not popup.property("_needsScroll")
    assert not popup.property("isOpen")

    _set_long_split_state(root, button)
    _pump(20)
    _assert_dropdown_parent_bindings(button, dropdown)
    _assert_dropdown_idle(dropdown)
    assert dropdown.property("textColor") == root.property("expectedDropdownTextColor")
    assert popup.property("_itemsHeight") > popup.property("availableContentHeight")
    assert popup.property("popupHeight") == root.property("expectedPopupMaxHeight")
    assert popup.property("_needsScroll")
    assert not popup.property("isOpen")
    assert _new_visible_windows(windows_before) == []


def test_custom_button_core_color_picker_parent_chain_remains_stable(
    button_leaf_scene,
):
    root, windows_before = button_leaf_scene
    picker = root.findChild(QObject, "screenPicker")
    assert picker is not None
    button = _custom_button_core(picker)
    assert picker.property("type") == root.property("expectedScreenPickerType")
    assert (button.property("width"), button.property("height")) == (
        picker.property("width"), picker.property("height"))
    assert (button.property("contentWidth"), button.property("contentHeight")) == (
        root.property("expectedButtonMinWidth"), root.property("expectedInputHeight"))
    assert button.property("buttonState") == "normal"
    assert not button.property("hovered")
    assert not button.property("pressed")
    assert not button.property("hasIcon")
    assert button.property("contentOffsetX") == 0
    assert button.property("opacity") == pytest.approx(1.0)

    picker.setProperty("enabled", False)
    _pump(20)
    assert not button.property("enabled")
    assert button.property("buttonState") == "disabled"
    assert button.property("opacity") == pytest.approx(0.6)
    assert _new_visible_windows(windows_before) == []


def test_button_leaf_sources_use_standard_sections():
    for source_path in BUTTON_SOURCES:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009"}
        ] == []
