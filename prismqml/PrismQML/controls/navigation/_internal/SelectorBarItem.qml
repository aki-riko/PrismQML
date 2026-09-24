// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../data"

// SelectorBarItem - SelectorBar delegate 选择条项委托
// Keeps delegate visuals and interaction separate from control orchestration.
// 将委托视觉与交互从控件编排中分离。
Item {
    id: selectorItem

    // ==================== Required Props 必需属性 ====================
    required property var selectorBar
    required property int index
    required property var modelData

    // ==================== Internal Props 内部属性 ====================
    property bool selected: index === selectorBar.currentIndex
    property bool hovered: hoverHandler.hovered
    property bool pressed: tapHandler.pressed
    property string itemText:
        typeof modelData === "string" ? modelData
        : (modelData && modelData.text !== undefined ? modelData.text : "")
    property string itemIcon:
        modelData && modelData.icon !== undefined ? modelData.icon : ""
    property string key:
        modelData && modelData.key !== undefined ? modelData.key
        : (itemText !== "" ? itemText : itemIcon)
    property bool hasIcon: itemIcon !== ""
    property bool hasText: itemText !== ""

    // ==================== Readonly State 只读状态 ====================
    // Vertical stacks content-sized cells, so the cell height stops depending on
    // the control height. 纵向堆叠按内容定宽的单元, 单元高度不再取自控件高度。
    readonly property bool _vertical: selectorBar.vertical
    // Touch has no hover preview: on touch the hover treatment follows the press
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
    readonly property bool _touchActive: Touch.feedback(hovered, pressed)

    // ==================== Size 尺寸 ====================
    width: Math.max(Enums.controlSize.selectorBarMinItemWidth,
                    itemContent.implicitWidth + Enums.spacing.l * 2)
    height: _vertical ? Enums.controlSize.selectorBarHeight : selectorBar.height

    // ==================== Content 内容 ====================
    // Hover/Press background for non-selected items 非选中项的悬停/按下背景
    Rectangle {
        anchors.fill: parent
        radius: Enums.surfaceRadius(Enums.radius.small)
        visible: !selectorItem.selected && (selectorItem._touchActive || selectorItem.pressed)
        color: {
            if (selectorItem.pressed) return Enums.stateColor.selectorBarItemPressed
            if (selectorItem._touchActive) return Enums.stateColor.selectorBarItemHover
            return Enums.transparent
        }
    }

    // Content row (icon + text) 内容行
    Row {
        id: itemContent
        anchors.centerIn: parent
        spacing: (selectorItem.hasIcon && selectorItem.hasText) ? Enums.spacing.s : 0

        Icon {
            icon: selectorItem.itemIcon
            iconSize: selectorItem.selectorBar.iconSize
            color: textItem.color
            visible: selectorItem.hasIcon
            anchors.verticalCenter: parent.verticalCenter
        }

        Label {
            id: textItem
            type: Enums.label.type_body
            text: selectorItem.itemText
            font.pixelSize: selectorItem.selectorBar.itemFontSize
            // The selected cell is the only bold one 只有选中项是粗体
            font.bold: selectorItem.selected
            visible: selectorItem.hasText
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    // HoverHandler for stable hover 使用HoverHandler实现稳定hover
    HoverHandler {
        id: hoverHandler
        cursorShape: Qt.PointingHandCursor
    }

    // TapHandler for click 使用TapHandler处理点击
    TapHandler {
        id: tapHandler
        onTapped: {
            if (index !== selectorBar.currentIndex) {
                selectorBar.setCurrentIndex(index)
                selectorBar.itemClicked(index, true)
            }
        }
    }
}
