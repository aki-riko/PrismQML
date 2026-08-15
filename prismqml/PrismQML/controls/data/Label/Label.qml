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
    
    // ==================== Public Props 公开属性 ====================
    property int type: Enums.label.type_body  // Default body type 默认正文类型
    property url url: ""
    property bool underlineOnHover: false  // Show only on hover when enabled 启用后仅悬停时显示下划线
    // Custom text color 自定义文本颜色
    property color customTextColor: Enums.transparent

    // ==================== Internal Props 内部属性 ====================
    property bool _useCustomColor: customTextColor != Enums.transparent

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isHyperlink: type === Enums.label.type_hyperlink
    readonly property bool hovered: _mouseArea.item
        ? _mouseArea.item.containsMouse
        : false
    readonly property bool pressed: _mouseArea.item
        ? _mouseArea.item.pressed
        : false
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

    readonly property color _interactiveTextColor: {
        if (!_isHyperlink || !pressed) return _textColor
        return Qt.darker(_textColor, 1.12)
    }

    // ==================== Signals 信号 ====================
    signal clicked()

    // ==================== Public Methods 公开方法 ====================
    // Clear text content 清空文本内容
    function clear() { text = "" }

    function getText() { return text }

    function getUrl() { return url }

    // Set word wrap 设置自动换行
    function setWordWrap(wrap) { wrapMode = wrap ? Text.WordWrap : Text.NoWrap }

    // Style bindings 样式绑定
    font.family: Enums.fontFamily
    font.pixelSize: _fontSize
    font.weight: _fontWeight
    font.underline: _isHyperlink && (!underlineOnHover || hovered)
    color: _interactiveTextColor
    scale: _isHyperlink && pressed ? 0.97 : 1
    wrapMode: (type === Enums.label.type_body || type === Enums.label.type_body_strong || type === Enums.label.type_body_small)
              ? Text.WordWrap : Text.NoWrap
    elide: type === Enums.label.type_display ? Text.ElideRight : Text.ElideNone

    Behavior on scale {
        NumberAnimation {
            duration: Enums.duration.ultraFast
            easing.type: Easing.OutQuad
        }
    }

    // ==================== Content 内容 ====================
    // Hyperlink interaction 超链接交互
    Loader {
        id: _mouseArea
        anchors.fill: parent
        active: _isHyperlink

        sourceComponent: MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor

            onClicked: {
                control.clicked()
                if (control.url.toString()) {
                    Qt.openUrlExternally(control.url)
                }
            }
        }
    }
}
