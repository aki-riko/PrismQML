// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/icons"
import "../controls/data/Label"

// ToggleNavigationBarItem - Toggle navigation bar row 切换导航栏项
// Horizontal layout: icon+text, hover/pressed states 水平布局: 图标+文字, 悬停/按下态
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string text: ""
    property string icon: ""
    property bool selected: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool hovered: hoverHandler.hovered
    readonly property bool pressed: tapHandler.pressed
    // Intrinsic width, so hosts can size to content instead of filling.
    // 固有宽度, 便于宿主按内容而非填充来定宽。
    readonly property real contentWidth: navContent.implicitWidth

    // ==================== Signals 信号 ====================
    signal clicked()

    height: Enums.controlSize.buttonHeight

    // ==================== Content 内容 ====================
    Rectangle {
        anchors.fill: parent
        radius: Enums.radius.small
        visible: !control.selected && (control.hovered || control.pressed)
        color: control.pressed ? Enums.stateColor.transparentPressed :
               control.hovered ? Enums.stateColor.transparentHover :
               Enums.transparent
    }

    Row {
        id: navContent
        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        spacing: control.icon !== "" && control.text !== "" ? Enums.spacing.s : 0

        Icon {
            icon: control.icon
            iconSize: Enums.iconSize.m
            color: control.selected ? Enums.accentForeground : Enums.textColor.primary
            visible: control.icon !== ""
            anchors.verticalCenter: parent.verticalCenter
        }

        Label {
            type: Enums.label.type_body
            text: control.text
            color: control.selected ? Enums.accentForeground : Enums.textColor.primary
            visible: control.text !== ""
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    HoverHandler { id: hoverHandler; cursorShape: Qt.PointingHandCursor }
    TapHandler {
        id: tapHandler
        onTapped: control.clicked()
    }
}
