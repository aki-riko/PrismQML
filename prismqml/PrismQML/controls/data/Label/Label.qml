// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../../SkinResolver.js" as SkinResolver

// Label - Unified label component 统一标签组件
// Usage: Label { type: Enums.label.type_body; text: "Hello" }
// For hyperlink: Label { type: Enums.label.type_hyperlink; text: "Link"; url: "https://..." }
Text {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var skinContext: null
    property int type: effectiveSkinContext.label.type_body  // Default body type 默认正文类型
    property url url: ""
    property bool underlineOnHover: true  // Show underline only on hover by default 默认仅悬停时显示下划线
    // Custom text color 自定义文本颜色
    property color customTextColor: effectiveSkinContext.transparent

    // ==================== Internal Props 内部属性 ====================
    property var _nearestSkinContext: null
    property bool _useCustomColor: customTextColor != effectiveSkinContext.transparent

    // ==================== Readonly State 只读状态 ====================
    readonly property var effectiveSkinContext:
        skinContext || _nearestSkinContext || Enums
    readonly property bool _isHyperlink: type === effectiveSkinContext.label.type_hyperlink
    readonly property bool hovered: _mouseArea.item
        ? _mouseArea.item.containsMouse
        : false
    readonly property bool pressed: _mouseArea.item
        ? _mouseArea.item.pressed
        : false
    readonly property int _fontSize: {
        switch (type) {
            case effectiveSkinContext.label.type_body:
            case effectiveSkinContext.label.type_body_strong:
            case effectiveSkinContext.label.type_hyperlink:
                return effectiveSkinContext.typography.body
            case effectiveSkinContext.label.type_body_small:
                return effectiveSkinContext.typography.bodySmall
            case effectiveSkinContext.label.type_caption:
                return effectiveSkinContext.typography.caption
            case effectiveSkinContext.label.type_subtitle:
                return effectiveSkinContext.typography.titleLarge
            case effectiveSkinContext.label.type_title:
                return effectiveSkinContext.typography.displayLarge
            case effectiveSkinContext.label.type_title_large:
                return effectiveSkinContext.typography.giant
            case effectiveSkinContext.label.type_display:
                return effectiveSkinContext.typography.mega
            default:
                return effectiveSkinContext.typography.body
        }
    }
    
    readonly property int _fontWeight: {
        switch (type) {
            case effectiveSkinContext.label.type_body_strong:
            case effectiveSkinContext.label.type_subtitle:
            case effectiveSkinContext.label.type_title:
            case effectiveSkinContext.label.type_title_large:
                return Font.DemiBold
            case effectiveSkinContext.label.type_display:
                return Font.Bold
            default:
                return Font.Normal
        }
    }
    
    readonly property color _textColor: {
        if (_useCustomColor) return customTextColor
        switch (type) {
            case effectiveSkinContext.label.type_hyperlink:
                return effectiveSkinContext.accentColor
            case effectiveSkinContext.label.type_caption:
                return effectiveSkinContext.textColor.secondary
            case effectiveSkinContext.label.type_body:
            case effectiveSkinContext.label.type_body_strong:
            case effectiveSkinContext.label.type_body_small:
                return effectiveSkinContext.stateColor.textStrong
            default:
                return effectiveSkinContext.textColor.primary
        }
    }

    readonly property color _interactiveTextColor: {
        if (!_isHyperlink) return _textColor
        if (pressed) {
            return _useCustomColor
                ? Qt.darker(_textColor, 1.12)
                : effectiveSkinContext.accentColorDark
        }
        if (hovered) {
            return _useCustomColor
                ? Qt.lighter(_textColor, 1.08)
                : effectiveSkinContext.accentColorLight
        }
        return _textColor
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

    function _resolveSkinContext() {
        if (skinContext) {
            _nearestSkinContext = null
            return
        }
        _nearestSkinContext = SkinResolver.nearestContext(parent)
    }

    // Style bindings 样式绑定
    font.family: effectiveSkinContext.fontFamily
    font.pixelSize: _fontSize
    font.weight: _fontWeight
    font.underline: _isHyperlink && (!underlineOnHover || hovered)
    color: _interactiveTextColor
    wrapMode: (type === effectiveSkinContext.label.type_body || type === effectiveSkinContext.label.type_body_strong || type === effectiveSkinContext.label.type_body_small)
              ? Text.WordWrap : Text.NoWrap
    elide: type === effectiveSkinContext.label.type_display ? Text.ElideRight : Text.ElideNone

    onParentChanged: _resolveSkinContext()
    onSkinContextChanged: _resolveSkinContext()
    Component.onCompleted: _resolveSkinContext()

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
