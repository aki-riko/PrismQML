// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../data"

// SegmentedItem - Segmented control delegate 分段控件委托
// Keeps delegate visuals and interaction separate from control orchestration.
// 将委托视觉与交互从控件编排中分离。
Item {
    id: segmentItem

    // ==================== Required Props 必需属性 ====================
    required property var segmentedControl
    required property int index
    required property var modelData

    // ==================== Internal Props 内部属性 ====================
    property bool selected: index === segmentedControl.currentIndex
    property bool hovered: hoverHandler.hovered
    property bool pressed: tapHandler.pressed
    property string itemText: typeof modelData === "string" ? modelData : (modelData && modelData.text !== undefined ? modelData.text : "")
    property string itemIcon: modelData && modelData.icon !== undefined ? modelData.icon : ""
    property string key: modelData && modelData.key !== undefined ? modelData.key : (itemText !== "" ? itemText : itemIcon)
    property bool hasIcon: itemIcon !== ""
    property bool hasText: itemText !== ""

    // ==================== Readonly State 只读状态 ====================
    // Vertical stacks content-sized cells, so the cell height stops depending on
    // the control height. 纵向堆叠按内容定宽的单元, 单元高度不再取自控件高度。
    readonly property bool _vertical: segmentedControl.vertical
    // Touch has no hover preview: on touch the hover treatment follows the press
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
    readonly property bool _touchActive: Touch.feedback(hovered, pressed)

    // ==================== Size 尺寸 ====================
    width: Math.max(Enums.controlSize.segmentedMinWidth, itemContent.implicitWidth + Enums.spacing.l * 2)
    height: _vertical
        ? Enums.controlSize.segmentedHeight - Enums.spacing.xxs * 2
        : segmentedControl.height - Enums.spacing.xxs * 2
    onSelectedChanged: if (selected) segmentedControl._scheduleSlideSync(false)
    onWidthChanged: if (selected) segmentedControl._scheduleSlideSync(false)
    onXChanged: if (selected) segmentedControl._scheduleSlideSync(false)
    // Cross-axis triggers are vertical-only so horizontal stays untouched
    // 副轴触发仅在纵向启用, 横向行为保持不变
    onHeightChanged: if (selected && _vertical) segmentedControl._scheduleSlideSync(false)
    onYChanged: if (selected && _vertical) segmentedControl._scheduleSlideSync(false)
    Component.onCompleted: if (selected) segmentedControl._scheduleSlideSync(false)

    // ==================== Content 内容 ====================
    // Hover/Press background for non-selected items 非选中项的悬停/按下背景
    Rectangle {
        anchors.fill: parent
        radius: Enums.surfaceRadius(Enums.radius.small)
        visible: !segmentItem.selected && (segmentItem._touchActive || segmentItem.pressed)
        color: {
            if (segmentItem.pressed) return Enums.stateColor.segmentedPressed
            if (segmentItem._touchActive) return Enums.stateColor.segmentedHover
            return Enums.transparent
        }
    }

    // Content row (icon + text) 内容行
    Row {
        id: itemContent
        anchors.centerIn: parent
        spacing: (segmentItem.hasIcon && segmentItem.hasText) ? Enums.spacing.s : 0

        Icon {
            id: iconItem
            icon: segmentItem.itemIcon
            iconSize: segmentedControl.iconSize
            color: textItem.color
            visible: segmentItem.hasIcon
            anchors.verticalCenter: parent.verticalCenter
        }

        Label {
            id: textItem
            type: Enums.label.type_body
            text: segmentItem.itemText
            font.pixelSize: segmentedControl.itemFontSize
            visible: segmentItem.hasText
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
            if (index !== segmentedControl.currentIndex) {
                segmentedControl.setCurrentIndex(index)
                segmentedControl.itemClicked(index, true)
            }
        }
    }
}
