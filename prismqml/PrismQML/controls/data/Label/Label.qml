// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// Label - Unified label component 统一标签组件
// Usage: Label { type: Enums.label.type_body; text: "Hello" }
// For hyperlink: Label { type: Enums.label.type_hyperlink; text: "Link"; url: "https://..." }
Text {
    id: control
    
    // ==================== Type Props 类型属性 ====================
    property int type: Enums.label.type_body  // Default body type 默认正文类型
    
    // ==================== Hyperlink Props 超链接属性 ====================
    property url url: ""
    property bool underlineOnHover: true
    readonly property bool hovered: _mouseArea.containsMouse

    // Custom text color 自定义文本颜色
    property color customTextColor: Enums.transparent
    property bool _useCustomColor: customTextColor != Qt.rgba(0, 0, 0, 0)

    signal clicked()
    
    // ==================== Style Binding 样式绑定 ====================
    font.family: Enums.fontFamily
    font.pixelSize: _fontSize
    font.weight: _fontWeight
    font.underline: type === Enums.label.type_hyperlink && hovered && underlineOnHover
    color: _textColor
    wrapMode: (type === Enums.label.type_body || type === Enums.label.type_body_strong || type === Enums.label.type_body_small)
              ? Text.WordWrap : Text.NoWrap
    elide: type === Enums.label.type_display ? Text.ElideRight : Text.ElideNone
    
    // ==================== Internal Style Calc 内部样式计算 ====================
    readonly property int _fontSize: {
        switch (type) {
            case Enums.label.type_body:
            case Enums.label.type_body_strong:
            case Enums.label.type_hyperlink:
                return Enums.typography.body
            case Enums.label.type_body_small:
                return Enums.typography.bodySmall
            case Enums.label.type_caption:
                return Enums.typography.caption
            case Enums.label.type_subtitle:
                return Enums.typography.titleLarge
            case Enums.label.type_title:
                return Enums.typography.displayLarge
            case Enums.label.type_title_large:
                return Enums.typography.giant
            case Enums.label.type_display:
                return Enums.typography.mega
            default:
                return Enums.typography.body
        }
    }
    
    readonly property int _fontWeight: {
        switch (type) {
            case Enums.label.type_body_strong:
            case Enums.label.type_subtitle:
            case Enums.label.type_title:
            case Enums.label.type_title_large:
                return Font.DemiBold
            case Enums.label.type_display:
                return Font.Bold
            default:
                return Font.Normal
        }
    }
    
    readonly property color _textColor: {
        if (_useCustomColor) return customTextColor
        switch (type) {
            case Enums.label.type_hyperlink:
                return Enums.accentColor
            case Enums.label.type_caption:
                return Enums.textColor.secondary
            case Enums.label.type_body:
            case Enums.label.type_body_strong:
            case Enums.label.type_body_small:
                return Enums.stateColor.textStrong
            default:
                return Enums.textColor.primary
        }
    }
    
    // ==================== Public Methods 公开方法 ====================
    // Clear text content 清空文本内容
    function clear() { text = "" }

    // ==================== Public Methods 公共方法 ====================
    function getText() { return text }
    
    
    function getUrl() { return url }
    
    
    // Set word wrap 设置自动换行
    function setWordWrap(wrap) { wrapMode = wrap ? Text.WordWrap : Text.NoWrap }
    
    // ==================== Hyperlink Interaction 超链接交互 ====================
    MouseArea {
        id: _mouseArea
        anchors.fill: parent
        hoverEnabled: type === Enums.label.type_hyperlink
        enabled: type === Enums.label.type_hyperlink
        visible: type === Enums.label.type_hyperlink
        cursorShape: type === Enums.label.type_hyperlink ? Qt.PointingHandCursor : Qt.ArrowCursor
        
        onClicked: {
            control.clicked()
            if (control.url.toString()) {
                Qt.openUrlExternally(control.url)
            }
        }
    }
}
