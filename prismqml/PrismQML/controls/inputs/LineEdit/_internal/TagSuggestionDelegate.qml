// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data"

// TagSuggestionDelegate - Single suggestion item delegate 单个建议项代理
// Separate file to avoid scope issues in PopupWindowCore 独立文件避免PopupWindowCore作用域问题
Rectangle {
    id: delegateRoot
    
    // ==================== Public Props 公开属性 ====================
    property string itemText: ""
    property bool selected: false

    // ==================== Readonly State 只读状态 ====================
    // Touch has no hover preview: on touch the hover treatment follows the press
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
    readonly property bool _touchActive: Touch.feedback(mouseArea.containsMouse, mouseArea.pressed)

    // ==================== Signals 信号 ====================
    signal itemClicked(string text)

    
    // ==================== Size 尺寸 ====================
    height: Enums.controlSize.inputHeight

    // Visual style 视觉样式
    radius: Enums.radius.small
    color: mouseArea.pressed ? Enums.stateColor.menuItemPressed
         : (delegateRoot._touchActive || delegateRoot.selected) ? Enums.stateColor.menuItemHover
         : Enums.transparent
    
    // ==================== Content 内容 ====================
    Label {
        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        type: Enums.label.type_caption
        text: delegateRoot.itemText
    }
    
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: delegateRoot.itemClicked(delegateRoot.itemText)
    }
}
