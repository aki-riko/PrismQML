// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import "../../icons"
import "../../data"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ListWidgetItem - Single item in ListWidget 列表控件单项
// Fluent Design style with indicator, reveal highlight, and press feedback
Rectangle {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property int itemIndex
    required property var itemData

    // ==================== Public Props 公开属性 ====================
    property bool selected: false
    property bool hovered: false
    property bool pressed: itemArea.pressed

    // ==================== Readonly State 只读状态 ====================
    // Compose every state into an opaque color so ColorAnimation does not flash dirty gray 将所有状态合成为不透明颜色，避免插值时闪过脏灰
    readonly property color _bgColor: {
        var base = Enums.cardColor
        if (selected) {
            return hovered ? Enums.stateColor.selectedHover
                           : Enums.stateColor.selected
        }
        if (pressed) return Qt.tint(base, Enums.stateColor.listItemPressed)
        if (hovered) return Qt.tint(base, Enums.stateColor.listItemHover)
        return base
    }
    readonly property color _revealGlowColor: Enums.stateColor.listItemRevealGlow

    // ==================== Signals 信号 ====================
    signal clicked()
    signal doubleClicked()

    // Reset transient state when ListView recycles the delegate ListView 回收委托时重置瞬态状态
    ListView.onPooled: root.hovered = false
    ListView.onReused: root.hovered = false

    // ==================== Size 尺寸 ====================
    height: Enums.controlSize.listItemHeight

    // ==================== Press Scale 按压缩放 ====================
    scale: pressed ? 0.98 : 1.0
    Behavior on scale {
        NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic }
    }
    transformOrigin: Item.Center

    // ==================== Background 背景 ====================
    color: _bgColor
    radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.card

    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }

    // ==================== Reveal Highlight 悬浮光晕 ====================
    Item {
        anchors.fill: parent
        clip: true
        visible: hovered && !pressed

        Rectangle {
            id: revealGlow
            width: Enums.controlSize.listRevealDiameter
            height: width
            radius: width / 2
            x: itemArea.mouseX - width / 2
            y: itemArea.mouseY - height / 2
            color: root._revealGlowColor

            opacity: hovered ? 1 : 0
            Behavior on opacity {
                NumberAnimation { duration: Enums.duration.normal; easing.type: Easing.OutCubic }
            }
        }
    }

    // ==================== Selection Indicator 选中指示条 ====================
    Rectangle {
        id: indicator
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        width: Enums.border.thick
        height: pressed ? root.height * Enums.listIndicator.pressedRatio : root.height * Enums.listIndicator.normalRatio
        radius: Enums.radius.micro
        color: Enums.accentColor

        opacity: selected ? 1 : 0
        scale: selected ? 1 : 0
        transformOrigin: Item.Center

        Behavior on height { NumberAnimation { duration: Enums.duration.fast } }
        Behavior on opacity {
            NumberAnimation { duration: selected ? Enums.duration.medium : Enums.duration.fast; easing.type: Easing.OutCubic }
        }
        Behavior on scale {
            NumberAnimation { duration: Enums.duration.spring; easing.type: Easing.OutBack }
        }
    }

    // ==================== Content Row 内容行 ====================
    Row {
        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.listItemPadding
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.listItemPadding
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.spacing.m

        Icon {
            id: iconItem

            property string _iconValue: {
                if (typeof itemData === "object" && itemData !== null) {
                    return itemData.icon || itemData.iconSource || ""
                }
                return ""
            }

            anchors.verticalCenter: parent.verticalCenter
            icon: _iconValue
            iconSize: Enums.iconSize.m
            color: Enums.textColor.primary
            visible: _iconValue !== ""
        }

        Label {
            property string _displayText: {
                if (typeof itemData === "object" && itemData !== null) {
                    return itemData.text || itemData.label || itemData.name || ""
                }
                return String(itemData || "")
            }

            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - (iconItem.visible ? iconItem.width + parent.spacing : 0)
            type: Enums.label.type_caption
            text: _displayText
            elide: Text.ElideRight
        }
    }

    // ==================== Mouse Area 鼠标区域 ====================
    MouseArea {
        id: itemArea
        anchors.fill: parent
        hoverEnabled: true

        onEntered: root.hovered = true
        onExited: root.hovered = false
        onClicked: root.clicked()
        onDoubleClicked: root.doubleClicked()
    }
}
