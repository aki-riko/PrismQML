// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "../../data"

// LineEditLabel - Floating label input 浮动标签输入
// Internal module for LineEdit LineEdit内部模块
Item {
    id: labelInput
    
    // ==================== Required Props 必需属性 ====================
    required property string label
    required property string placeholderText
    required property bool controlEnabled
    
    // Padding from InputCore 从基类继承的边距
    required property int paddingLeft
    required property int paddingRight
    
    // Text style from InputCore 从基类继承的文本样式
    required property string fontFamily
    required property int fontSize
    
    // ==================== Output Props 输出属性 ====================
    property alias text: inputField.text
    readonly property bool focused: inputField.activeFocus
    readonly property bool hovered: hoverHandler.hovered
    property alias textInput: inputField
    readonly property bool hasContent: inputField.text.length > 0 || focused
    
    // ==================== Signals 信号 ====================
    signal textModified(string newText)
    signal editingFinished()

    // ==================== Methods 方法 ====================
    function clear() { inputField.text = "" }
    function forceActiveFocus() { inputField.forceActiveFocus() }

    // ==================== Floating Label 浮动标签 ====================
    Label {
        id: floatingLabel
        type: Enums.label.type_caption
        x: labelInput.paddingLeft
        y: labelInput.hasContent ? Enums.spacing.s : (parent.height - height) / 2
        text: labelInput.label
        font.pixelSize: Enums.typography.body
        color: labelInput.focused ? Enums.accentColor : Enums.stateColor.textMedium
        // Use scale instead of font.pixelSize animation to avoid re-rasterization 使用 scale 代替 font.pixelSize 动画以避免重新光栅化

        scale: labelInput.hasContent ? (Enums.typography.caption / Enums.typography.body) : 1.0
        transformOrigin: Item.Left
        
        Behavior on y { NumberAnimation { duration: Enums.duration.normal; easing.type: Easing.OutCubic } }
        Behavior on scale { NumberAnimation { duration: Enums.duration.normal; easing.type: Easing.OutCubic } }
        Behavior on color { ColorAnimation { duration: Enums.duration.normal } }
    }
    
    // ==================== Input Field 输入框 ====================
    TextInput {
        id: inputField
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: labelInput.paddingLeft
        anchors.rightMargin: labelInput.paddingRight
        anchors.bottomMargin: Enums.spacing.m
        height: 24
        font.family: labelInput.fontFamily
        font.pixelSize: labelInput.fontSize
        color: Enums.textColor.primary
        enabled: labelInput.controlEnabled
        clip: true
        verticalAlignment: Text.AlignVCenter
        selectByMouse: true
        
        onTextChanged: labelInput.textModified(text)
        onEditingFinished: labelInput.editingFinished()
    }
    
    // ==================== Hover Detection 悬浮检测 ====================
    HoverHandler {
        id: hoverHandler
    }
}
