// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../../.."
import "../../../icons"
import "../../../data/Label"

// SearchResultItem — 单条搜索结果 delegate
//
// 布局: [Icon] [title(高亮匹配字符) + subtitle] [section badge]
// hover/selected 状态 alpha 叠加,跟 ListWidgetItem 视觉一致.
//
// 高亮: 用 Text.RichText + HTML <b style='color:accent'> 渲染匹配字符.
// title 字段需通过 fieldRanges 拿到匹配位置后由父 list 拼好富文本.
Rectangle {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property int itemIndex
    required property var entryData      // 完整 entry: {title, subtitle, icon, section, ...}
    required property string highlightedTitle    // 已渲染好高亮的 HTML 字符串
    required property string highlightedSubtitle // 同上,subtitle 高亮

    // ==================== Internal Props 内部属性 ====================
    property bool hovered: false
    property bool selected: false
    property bool pressed: false

    // ==================== Readonly State 只读状态 ====================
    readonly property color _bgColor: {
        if (selected) {
            return hovered ? Enums.stateColor.selectedHover
                           : Enums.stateColor.selected
        }
        if (pressed) return Enums.stateColor.listItemPressed
        if (hovered) return Enums.stateColor.listItemHover
        return Enums.transparent
    }

    // ==================== Signals 信号 ====================
    signal clicked()
    signal hoveredChanged_()  // 跟 hover 状态防撞

    // ==================== Size 尺寸 ====================
    height: Enums.searchMetrics.resultItemHeight
    width: parent ? parent.width : 0

    // Background state layer, aligned with ListWidgetItem 背景状态层，与 ListWidgetItem 一致
    color: _bgColor
    radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.card

    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }

    // ==================== Content 内容 ====================
    // Selection indicator 左侧选中竖条
    Rectangle {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        width: Enums.searchMetrics.resultIndicatorWidth
        height: parent.height * 0.5
        radius: Enums.radius.micro
        color: Enums.accentColor
        visible: root.selected
        Behavior on height { NumberAnimation { duration: Enums.duration.fast } }
    }

    // Result content 搜索结果内容
    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Enums.spacing.l
        anchors.rightMargin: Enums.spacing.l
        spacing: Enums.spacing.m

        // 图标 (可选)
        Icon {
            Layout.preferredWidth: Enums.searchMetrics.resultIconSize
            Layout.preferredHeight: Enums.searchMetrics.resultIconSize
            Layout.alignment: Qt.AlignVCenter
            icon: root.entryData && root.entryData.icon ? root.entryData.icon : ''
            iconSize: Enums.searchMetrics.resultIconSize
            color: Enums.textColor.secondary
            visible: !!icon
        }

        // 主体: title + subtitle 两行
        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: Enums.spacing.xxs

            Label {
                Layout.fillWidth: true
                text: root.highlightedTitle
                textFormat: Text.RichText
                type: Enums.label.type_body
                color: Enums.textColor.primary
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
            }

            Label {
                Layout.fillWidth: true
                text: root.highlightedSubtitle
                textFormat: Text.RichText
                type: Enums.label.type_caption
                color: Enums.textColor.secondary
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
                visible: text.length > 0
            }
        }
    }

    // Mouse area 鼠标交互区
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onEntered: root.hovered = true
        onExited: root.hovered = false
        onPressedChanged: root.pressed = pressed
        onClicked: root.clicked()
    }
}
