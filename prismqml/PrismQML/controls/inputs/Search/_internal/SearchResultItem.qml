// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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

    // ==================== Required Props ====================
    required property int itemIndex
    required property var entryData      // 完整 entry: {title, subtitle, icon, section, ...}
    required property string highlightedTitle    // 已渲染好高亮的 HTML 字符串
    required property string highlightedSubtitle // 同上,subtitle 高亮

    // ==================== State ====================
    property bool hovered: false
    property bool selected: false
    property bool pressed: false

    // ==================== Signals ====================
    signal clicked()
    signal hoveredChanged_()  // 跟 hover 状态防撞

    // ==================== Size ====================
    height: 48
    width: parent ? parent.width : 0

    // ==================== Background (跟 ListWidgetItem 一致的状态层) ====================
    color: _bgColor
    radius: Enums.radius.card

    readonly property color _bgColor: {
        if (selected) {
            return hovered ? Enums.stateColor.selectedHover
                           : Enums.stateColor.selected
        }
        if (pressed) return Enums.stateColor.listItemPressed
        if (hovered) return Enums.stateColor.listItemHover
        return Enums.transparent
    }

    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }

    // ==================== Selection indicator (左侧竖条) ====================
    Rectangle {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        width: 3
        height: parent.height * 0.5
        radius: 1.5
        color: Enums.accentColor
        visible: root.selected
        Behavior on height { NumberAnimation { duration: Enums.duration.fast } }
    }

    // ==================== Content ====================
    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Enums.spacing.l
        anchors.rightMargin: Enums.spacing.l
        spacing: Enums.spacing.m

        // 图标 (可选)
        Icon {
            Layout.preferredWidth: 18
            Layout.preferredHeight: 18
            Layout.alignment: Qt.AlignVCenter
            icon: root.entryData && root.entryData.icon ? root.entryData.icon : ''
            iconSize: 18
            color: Enums.textColor.secondary
            visible: !!icon
        }

        // 主体: title + subtitle 两行
        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 2

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

    // ==================== Mouse area ====================
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
