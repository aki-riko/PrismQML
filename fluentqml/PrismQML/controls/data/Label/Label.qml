// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// Label - Unified label component 统一标签组件
// Usage: Label { type: Enums.label.type_body; text: "Hello" }
// For hyperlink: Label { type: Enums.label.type_hyperlink; text: "Link"; url: "https://..." }
Text {
    id: control
    
    // ==================== Type Props 类型属性 ====================
    property int type: 0  // Default: type_body 默认正文类型
    
    // ==================== Hyperlink Props 超链接属性 ====================
    property url url: ""
    property bool underlineOnHover: true
    signal clicked()
    readonly property bool hovered: _mouseArea.containsMouse
    
    // ==================== Internal Type Constants 内部类型常量 ====================
    readonly property int _type_body: 0
    readonly property int _type_body_strong: 1
    readonly property int _type_body_small: 2
    readonly property int _type_caption: 3
    readonly property int _type_subtitle: 4
    readonly property int _type_title: 5
    readonly property int _type_title_large: 6
    readonly property int _type_display: 7
    readonly property int _type_hyperlink: 8
    
    // ==================== Style Binding 样式绑定 ====================
    font.family: Enums.fontFamily
    font.pixelSize: _fontSize
    font.weight: _fontWeight
    font.underline: type === _type_hyperlink && hovered && underlineOnHover
    color: _textColor
    wrapMode: (type === _type_body || type === _type_body_strong || type === _type_body_small) 
              ? Text.WordWrap : Text.NoWrap
    elide: type === _type_display ? Text.ElideRight : Text.ElideNone
    
    // ==================== Internal Style Calc 内部样式计算 ====================
    readonly property int _fontSize: {
        switch (type) {
            case _type_body:
            case _type_body_strong:
            case _type_hyperlink:
                return Enums.typography.body
            case _type_body_small:
                return Enums.typography.bodySmall
            case _type_caption:
                return Enums.typography.caption
            case _type_subtitle:
                return Enums.typography.titleLarge
            case _type_title:
                return Enums.typography.displayLarge
            case _type_title_large:
                return Enums.typography.giant
            case _type_display:
                return Enums.typography.mega
            default:
                return Enums.typography.body
        }
    }
    
    readonly property int _fontWeight: {
        switch (type) {
            case _type_body_strong:
            case _type_subtitle:
            case _type_title:
            case _type_title_large:
                return Font.DemiBold
            case _type_display:
                return Font.Bold
            default:
                return Font.Normal
        }
    }
    
    readonly property color _textColor: {
        if (_useCustomColor) return customTextColor
        switch (type) {
            case _type_hyperlink:
                return Enums.accentColor
            case _type_caption:
                return Enums.textColor.secondary
            case _type_body:
            case _type_body_strong:
            case _type_body_small:
                return Enums.stateColor.textStrong
            default:
                return Enums.textColor.primary
        }
    }
    
    // ==================== Public Methods 公开方法 ====================
    // Clear text content 清空文本内容
    function clear() { text = "" }

    // Custom text color 自定义文本颜色
    property color customTextColor: "transparent"
    property bool _useCustomColor: customTextColor != Qt.rgba(0, 0, 0, 0)

    // ==================== Public Methods 公共方法 ====================
    function getText() { return text }
    
    
    function getUrl() { return url }
    
    
    // Set word wrap 设置自动换行
    function setWordWrap(wrap) { wrapMode = wrap ? Text.WordWrap : Text.NoWrap }
    
    // ==================== Hyperlink Interaction 超链接交互 ====================
    MouseArea {
        id: _mouseArea
        anchors.fill: parent
        hoverEnabled: type === _type_hyperlink
        enabled: type === _type_hyperlink
        visible: type === _type_hyperlink
        cursorShape: type === _type_hyperlink ? Qt.PointingHandCursor : Qt.ArrowCursor
        
        onClicked: {
            control.clicked()
            if (control.url.toString()) {
                Qt.openUrlExternally(control.url)
            }
        }
    }
}
