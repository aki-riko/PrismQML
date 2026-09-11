# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML scene data strings used by combo_box_core_conventions_shared."""

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int expectedPopupPadding: Enums.comboBoxMetrics.popupPadding
    readonly property int expectedPanelOffset: Enums.popupMetrics.panelOffset

    function useEnglish() { Translator.setLanguage(Enums.lang.en) }
    function useSimplifiedChinese() { Translator.setLanguage(Enums.lang.zh_CN) }

    property var probeValues: []

    // Objects are passed in as arguments: this fixture builds the scene with
    // rootContext, where ids are not resolvable inside function bodies.
    function replaceModelOnly(holder, values) {
        holder.values = values
    }

    function replaceModelAndSetIndex(holder, core, entry, values, index) {
        holder.values = values
        core.currentIndex = index
        entry.currentIndex = index
    }

    width: 720
    height: 360
    visible: true

    QtObject {
        id: modelHolder
        objectName: "modelHolder"
        property var values: ["First", "Second"]
    }

    ComboBoxCore {
        objectName: "replacingCombo"
        x: 60
        y: 140
        width: 260
        model: modelHolder.values
        currentIndex: 0
    }

    ComboBox {
        objectName: "replacingEntryCombo"
        x: 60
        y: 190
        width: 260
        model: modelHolder.values
        currentIndex: 0
    }

    ComboBoxCore {
        id: combo
        objectName: "combo"
        x: 60
        y: 60
        width: 260
        model: [
            {"text": "Alpha", "data": 10, "icon": "alpha-icon"},
            {"text": "Beta", "data": 20, "icon": "beta-icon", "enabled": false},
            {"text": "Gamma", "data": 30, "icon": "gamma-icon"}
        ]
        currentIndex: 0
        maxVisibleItems: 3
        popupItemHeight: 40
    }

    ComboBoxCore {
        id: editableCombo
        objectName: "editableCombo"
        x: 380
        y: 60
        width: 260
        model: ["Alpha", "Beta", "Gamma"]
        currentIndex: 0
        editable: true
    }

    ComboBoxCore {
        objectName: "translatedCombo"
        currentIndex: -1
        visible: false
    }

    ComboBoxCore {
        objectName: "customPlaceholderCombo"
        currentIndex: -1
        placeholderText: "Choose a value"
        visible: false
    }
}
"""
