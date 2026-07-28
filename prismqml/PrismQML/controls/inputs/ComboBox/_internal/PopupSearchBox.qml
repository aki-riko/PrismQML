// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../.."

// PopupSearchBox - Reusable search box for popup content 弹出内容复用搜索框
// Internal component for ComboBox popups ComboBox弹出框内部组件
Item {
    id: searchBox

    // ==================== Public Props 公开属性 ====================
    property bool searchEnabled: true
    property string placeholderText: { Translator._v; return Translator.tr("placeholder_keyword") }
    property alias text: lineEdit.text
    
    // ==================== Signals 信号 ====================
    signal searchTextChanged(string text)
    signal searchTriggered(string text)

    // ==================== Public Methods 公开方法 ====================
    function clear() {
        lineEdit.text = ""
    }

    function focusInput() {
        lineEdit.forceActiveFocus()
    }

    // ==================== Size 尺寸 ====================
    width: parent ? parent.width : 0
    height: searchEnabled ? Enums.comboBoxMetrics.searchBoxHeight : 0
    visible: searchEnabled

    // ==================== Content 内容 ====================
    LineEdit {
        id: lineEdit
        anchors.fill: parent
        anchors.margins: Enums.spacing.m
        inputType: Enums.input.type_search
        placeholderText: searchBox.placeholderText
        
        onTextChanged: searchBox.searchTextChanged(text)
        onSearched: (text) => searchBox.searchTriggered(text)
    }
}
