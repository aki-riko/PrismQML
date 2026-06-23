// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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

    // ==================== State Props 状态属性 ====================
    property bool selected: false
    property bool hovered: false
    property bool pressed: itemArea.pressed

    // ==================== Recycling 回收重置 ====================
    ListView.onPooled: root.hovered = false
    ListView.onReused: root.hovered = false

    // ==================== Signals 信号 ====================
    signal clicked()
    signal doubleClicked()

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
    radius: Enums.radius.card

    // 状态色全部合成成不透明色, 在不透明色之间做 ColorAnimation 插值才平滑。
    // 若默认态用透明黑 (transparent = #00000000), 插值到浅蓝/灰时中间帧 RGB 从黑
    // 渐变且 alpha 低, 合成在白卡上会闪过一帧脏灰 -> 看起来像"灰块跳变"。
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

    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }

    // ==================== Reveal Highlight 悬浮光晕 ====================
    Item {
        anchors.fill: parent
        clip: true
        visible: hovered && !pressed

        Rectangle {
            id: revealGlow
            width: 120; height: 120
            radius: 60
            x: itemArea.mouseX - 60
            y: itemArea.mouseY - 60
            color: Enums.isDark ? Qt.rgba(1, 1, 1, 0.04) : Qt.rgba(0, 0, 0, 0.03)

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
            anchors.verticalCenter: parent.verticalCenter
            icon: _iconValue
            iconSize: Enums.iconSize.m
            color: Enums.textColor.primary
            visible: _iconValue !== ""

            property string _iconValue: {
                if (typeof itemData === "object" && itemData !== null) {
                    return itemData.icon || itemData.iconSource || ""
                }
                return ""
            }
        }

        Label {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - (iconItem.visible ? iconItem.width + parent.spacing : 0)
            type: Enums.label.type_caption
            text: _displayText
            elide: Text.ElideRight

            property string _displayText: {
                if (typeof itemData === "object" && itemData !== null) {
                    return itemData.text || itemData.label || itemData.name || ""
                }
                return String(itemData || "")
            }
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
