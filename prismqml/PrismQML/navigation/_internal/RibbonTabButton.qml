// RibbonTabButton - Ribbon strip tab button 功能区标签条按钮
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// Owns one tab of the ribbon strip; the bar keeps selection and ordering.
// 承载标签条上的单个标签, 选中与次序由功能区持有。
pragma ComponentBehavior: Bound
Item {
    id: control

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property int index
    required property var modelData

    // ==================== Public Props 公开属性 ====================
    property bool selected: index === control.host.currentIndex
    property bool hovered: tabHover.hovered
    property bool pressed: tabTap.pressed

    // ==================== Internal Props 内部属性 ====================
    // Touch has no hover preview: on touch the hover treatment follows the press
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
    readonly property bool _touchActive: Touch.feedback(hovered, pressed)

    // ==================== Readonly State 只读状态 ====================
    readonly property string tabTitle: control.modelData ? (control.modelData.title || "") : ""
    readonly property string tabIcon: control.modelData ? (control.modelData.icon || "") : ""
    readonly property color _backgroundColor: control.selected
        ? Enums.stateColor.cardDefaultBg
        : (control._touchActive ? Enums.stateColor.hover : Enums.transparent)
    readonly property color _textColor: control.selected
        ? Enums.textColor.primary
        : (control.enabled ? Enums.textColor.secondary : Enums.textColor.disabled)

    // ==================== Signals 信号 ====================
    signal activated(int index)

    // ==================== Size 尺寸 ====================
    implicitWidth: Math.max(Enums.controlSize.segmentedMinWidth,
        tabContent.implicitWidth + Enums.spacing.xl * 2)
    implicitHeight: Enums.controlSize.tabBarHeight
    width: implicitWidth
    height: implicitHeight

    // ==================== Content 内容 ====================
    Rectangle {
        id: tabBackground

        anchors.fill: parent
        color: control._backgroundColor
        radius: Enums.surfaceRadius(Enums.radius.small)

        HoverBehavior on color {
            active: control._touchActive && !control.pressed
            enterDuration: Enums.duration.fast
        }
    }

    Row {
        id: tabContent

        anchors.centerIn: parent
        spacing: Enums.spacing.xs

        Icon {
            anchors.verticalCenter: parent.verticalCenter
            iconSize: Enums.iconSize.m
            color: control._textColor
            icon: control.tabIcon
            visible: control.tabIcon !== ""
        }

        Label {
            anchors.verticalCenter: parent.verticalCenter
            type: Enums.label.type_body_small
            text: control.tabTitle
            customTextColor: control._textColor
        }
    }

    Rectangle {
        id: selectionIndicator

        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        width: Math.max(0, parent.width - Enums.spacing.l)
        height: Enums.border.normal
        radius: height / 2
        color: Enums.accentColor
        visible: control.selected
    }

    HoverHandler {
        id: tabHover
        cursorShape: Qt.PointingHandCursor
        enabled: control.enabled
    }

    TapHandler {
        id: tabTap
        enabled: control.enabled
        onTapped: control.activated(control.index)
    }
}
