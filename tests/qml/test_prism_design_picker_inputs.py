# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design picker input skin tests."""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


def _build(engine, qml: bytes):
    component = QQmlComponent(engine)
    component.setData(qml, QUrl("inline"))
    assert not component.isError(), [error.toString() for error in component.errors()]

    item = component.create(engine.rootContext())
    assert item is not None, [error.toString() for error in component.errors()]
    return component, item


def _build_file(engine, path: Path):
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(path)))
    assert not component.isError(), [error.toString() for error in component.errors()]

    item = component.create(engine.rootContext())
    assert item is not None, [error.toString() for error in component.errors()]
    return component, item


def _rgb(qcolor):
    return (
        round(qcolor.redF() * 255),
        round(qcolor.greenF() * 255),
        round(qcolor.blueF() * 255),
    )


def test_prism_design_datetime_picker_popup_selection_highlight(qapp):
    popup_path = (
        Path(__file__).resolve().parents[2]
        / "prismqml"
        / "PrismQML"
        / "controls"
        / "inputs"
        / "Picker"
        / "_internal"
        / "DateTimePickerPopup.qml"
    )

    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build_file(engine, popup_path))
        popup = keep[-1][1]
        assert _rgb(popup.property("_selectionHighlightColor")) == (212, 237, 234)

        setTheme(Theme.DARK)
        keep.append(_build_file(engine, popup_path))
        dark_popup = keep[-1][1]
        assert _rgb(dark_popup.property("_selectionHighlightColor")) == (22, 63, 67)
    finally:
        for component, item in reversed(keep):
            item.deleteLater()
            component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)


def test_prism_design_public_input_entries_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build_file(
            engine,
            Path(__file__).resolve().parents[2]
            / "prismqml"
            / "PrismQML"
            / "controls"
            / "inputs"
            / "ComboBox"
            / "ComboBoxCore.qml",
        ))
        direct_combo = keep[-1][1]
        direct_combo.setProperty("model", ["One", "Two"])
        direct_combo.setProperty("currentIndex", 1)
        assert direct_combo.property("radius") == 4
        assert direct_combo.property("currentText") == "Two"

        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    property int entryHeight: combo.implicitHeight
    property string entryText: combo.currentText
    property int multiRadius: multi.radius
    property int treeRadius: tree.radius
    property int treeFlatCount: tree._flatModel.length
    property int multiTreeRadius: multiTree.radius
    property int multiTreeFlatCount: multiTree._flatListModel.count
    property int fontRadius: fontCombo.radius
    property string fontName: fontCombo.currentFont

    ComboBox {
        id: combo
        model: ["Alpha", "Beta"]
        currentIndex: 1
        width: 180
    }

    ComboBoxMulti {
        id: multi
        model: ["Alpha", "Beta"]
        selectedIndices: [0]
        width: 220
    }

    ComboBoxTree {
        id: tree
        model: [{ "text": "Root", "children": [{ "text": "Leaf" }] }]
        width: 220
    }

    ComboBoxMultiTree {
        id: multiTree
        model: [{ "text": "Root", "children": [{ "text": "Leaf" }] }]
        selectedPaths: [["Root", "Leaf"]]
        width: 260
    }

    ComboBoxFont {
        id: fontCombo
        currentFont: "Consolas"
        width: 220
    }
}
"""))
        combo_family = keep[-1][1]
        qapp.processEvents()
        assert combo_family.property("entryHeight") == 32
        assert combo_family.property("entryText") == "Beta"
        assert combo_family.property("multiRadius") == 4
        assert combo_family.property("treeRadius") == 4
        assert combo_family.property("treeFlatCount") == 2
        assert combo_family.property("multiTreeRadius") == 4
        assert combo_family.property("multiTreeFlatCount") == 2
        assert combo_family.property("fontRadius") == 4
        assert combo_family.property("fontName") == "Consolas"

        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    property int filterRadius: filter.radius
    property color filterColor: filter.color
    property int spinRadius: spin.radius
    property color spinColor: spin.color
    property color spinTextColor: spin.inputTextColor
    property real spinValue: spin.value
    property int checkType: check.controlType
    property color checkColor: check._checkedColor
    property int radioType: radio.controlType
    property color radioColor: radio._checkedColor
    property int switchType: toggleSwitch.controlType
    property color switchColor: toggleSwitch._checkedColor

    FilterBar {
        id: filter
        items: ["All", "Open", "Closed"]
        currentIndex: 1
    }

    SpinBox {
        id: spin
        value: 4
        minimum: 0
        maximum: 10
    }

    CheckBox {
        id: check
        checked: true
        text: "Check"
    }

    RadioButton {
        id: radio
        checked: true
        text: "Radio"
    }

    ToggleSwitch {
        id: toggleSwitch
        checked: true
        text: "Switch"
    }
}
"""))
        choice_inputs = keep[-1][1]
        assert choice_inputs.property("filterRadius") == 4
        assert _rgb(choice_inputs.property("filterColor")) == (248, 250, 249)
        assert choice_inputs.property("spinRadius") == 4
        assert _rgb(choice_inputs.property("spinColor")) == (252, 254, 253)
        assert _rgb(choice_inputs.property("spinTextColor")) == (21, 35, 38)
        assert choice_inputs.property("spinValue") == 4
        assert choice_inputs.property("checkType") == 0
        assert _rgb(choice_inputs.property("checkColor")) == (22, 124, 128)
        assert choice_inputs.property("radioType") == 1
        assert _rgb(choice_inputs.property("radioColor")) == (22, 124, 128)
        assert choice_inputs.property("switchType") == 2
        assert _rgb(choice_inputs.property("switchColor")) == (22, 124, 128)

        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    property string searchQuery: search.query
    property string searchPlaceholder: search.placeholderText
    property int passwordStrength: strength.strength
    property color passwordStrongColor: strength.strengthColors[4]
    property int shortcutRadius: shortcut.radius
    property color shortcutColor: shortcut.color
    property string shortcutValue: shortcut.shortcut
    property int wheelIndex: wheel.currentIndex
    property string wheelValue: wheel.currentValue
    property int sliderBorderWidth: slider._handleBorderWidth
    property color sliderTrackColor: slider._trackColor
    property color sliderHandleColor: slider.handleColor
    property color mediaDividerColor: media._dividerColor
    property color mediaHandleColor: media._handleColor
    property color mediaHandleIconColor: media._handleIconColor

    LocalSearchBar {
        id: search
        entries: [{ "title": "Build" }, { "title": "Settings" }]
        placeholderText: "Search"
        popupMode: LocalSearchBar.CenteredOverlay
        Component.onCompleted: setQuery("prism")
    }

    PasswordStrengthIndicator {
        id: strength
        password: "PrismDesign2026!"
    }

    ShortcutEditor {
        id: shortcut
        shortcut: "Ctrl+K"
    }

    CycleWheelPicker {
        id: wheel
        items: ["One", "Two", "Three"]
        currentIndex: 1
    }

    Slider {
        id: slider
        value: 42
    }

    BeforeAfterSlider {
        id: media
        position: 0.4
    }
}
"""))
        utility_inputs = keep[-1][1]
        qapp.processEvents()
        assert utility_inputs.property("searchQuery") == "prism"
        assert utility_inputs.property("searchPlaceholder") == "Search"
        assert utility_inputs.property("passwordStrength") == 4
        assert _rgb(utility_inputs.property("passwordStrongColor")) == (15, 123, 15)
        assert utility_inputs.property("shortcutRadius") == 4
        assert _rgb(utility_inputs.property("shortcutColor")) == (252, 254, 253)
        assert utility_inputs.property("shortcutValue") == "Ctrl+K"
        assert utility_inputs.property("wheelIndex") == 1
        assert utility_inputs.property("wheelValue") == "Two"
        assert utility_inputs.property("sliderBorderWidth") == 1
        assert _rgb(utility_inputs.property("sliderTrackColor")) == (225, 233, 231)
        assert _rgb(utility_inputs.property("sliderHandleColor")) == (252, 254, 253)
        assert _rgb(utility_inputs.property("mediaDividerColor")) == (22, 124, 128)
        assert _rgb(utility_inputs.property("mediaHandleColor")) == (252, 254, 253)
        assert _rgb(utility_inputs.property("mediaHandleIconColor")) == (86, 106, 109)

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    property int comboRadius: combo.radius
    property color filterColor: filter.color
    property color spinColor: spin.color
    property color spinTextColor: spin.inputTextColor
    property color checkColor: check._checkedColor
    property color sliderTrackColor: slider._trackColor
    property color sliderHandleColor: slider.handleColor
    property color mediaDividerColor: media._dividerColor
    property color mediaHandleColor: media._handleColor
    property color mediaHandleIconColor: media._handleIconColor
    property color passwordStrongColor: strength.strengthColors[4]

    ComboBoxCore {
        id: combo
        model: ["One", "Two"]
        currentIndex: 1
    }

    FilterBar {
        id: filter
        items: ["All", "Open"]
        currentIndex: 1
    }

    SpinBox {
        id: spin
        value: 5
    }

    CheckBox {
        id: check
        checked: true
    }

    Slider {
        id: slider
        value: 42
    }

    BeforeAfterSlider {
        id: media
        position: 0.4
    }

    PasswordStrengthIndicator {
        id: strength
        password: "PrismDesign2026!"
    }
}
"""))
        dark_inputs = keep[-1][1]
        assert dark_inputs.property("comboRadius") == 4
        assert _rgb(dark_inputs.property("filterColor")) == (18, 25, 27)
        assert _rgb(dark_inputs.property("spinColor")) == (25, 34, 36)
        assert _rgb(dark_inputs.property("spinTextColor")) == (238, 245, 243)
        assert _rgb(dark_inputs.property("checkColor")) == (85, 214, 210)
        assert _rgb(dark_inputs.property("sliderTrackColor")) == (16, 23, 25)
        assert _rgb(dark_inputs.property("sliderHandleColor")) == (25, 34, 36)
        assert _rgb(dark_inputs.property("mediaDividerColor")) == (85, 214, 210)
        assert _rgb(dark_inputs.property("mediaHandleColor")) == (25, 34, 36)
        assert _rgb(dark_inputs.property("mediaHandleIconColor")) == (164, 181, 182)
        assert _rgb(dark_inputs.property("passwordStrongColor")) == (108, 203, 95)
    finally:
        for component, item in reversed(keep):
            item.deleteLater()
            component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)


def test_prism_design_image_cropper_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    property int previewRadius: cropper._previewRadius
    property color previewBackground: cropper._previewBackground
    property color previewBorder: cropper._previewBorderColor
    property color previewIcon: cropper._previewIconColor
    property color previewText: cropper._previewTextColor
    property color dialogBackground: cropper._dialogBackground
    property int dialogType: dialogCropper.type
    property int dialogPreviewRadius: dialogCropper._previewRadius

    ImageCropper {
        id: cropper
        type: Enums.imageCropper.type_overlay
    }

    ImageCropperDialog {
        id: dialogCropper
    }
}
"""))
        cropper = keep[-1][1]
        assert cropper.property("previewRadius") == 4
        assert _rgb(cropper.property("previewBackground")) == (248, 250, 249)
        assert _rgb(cropper.property("previewBorder")) == (221, 230, 228)
        assert _rgb(cropper.property("previewIcon")) == (22, 124, 128)
        assert _rgb(cropper.property("previewText")) == (86, 106, 109)
        assert _rgb(cropper.property("dialogBackground")) == (238, 243, 242)
        assert cropper.property("dialogType") == 0
        assert cropper.property("dialogPreviewRadius") == 4

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    property int previewRadius: cropper._previewRadius
    property color previewBackground: cropper._previewBackground
    property color previewBorder: cropper._previewBorderColor
    property color previewIcon: cropper._previewIconColor
    property color previewText: cropper._previewTextColor
    property color dialogBackground: cropper._dialogBackground
    property int dialogType: dialogCropper.type
    property int dialogPreviewRadius: dialogCropper._previewRadius

    ImageCropper {
        id: cropper
        type: Enums.imageCropper.type_overlay
    }

    ImageCropperDialog {
        id: dialogCropper
    }
}
"""))
        dark_cropper = keep[-1][1]
        assert dark_cropper.property("previewRadius") == 4
        assert _rgb(dark_cropper.property("previewBackground")) == (18, 25, 27)
        assert _rgb(dark_cropper.property("previewBorder")) == (34, 48, 51)
        assert _rgb(dark_cropper.property("previewIcon")) == (85, 214, 210)
        assert _rgb(dark_cropper.property("previewText")) == (164, 181, 182)
        assert _rgb(dark_cropper.property("dialogBackground")) == (13, 18, 19)
        assert dark_cropper.property("dialogType") == 0
        assert dark_cropper.property("dialogPreviewRadius") == 4
    finally:
        for component, item in reversed(keep):
            item.deleteLater()
            component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
