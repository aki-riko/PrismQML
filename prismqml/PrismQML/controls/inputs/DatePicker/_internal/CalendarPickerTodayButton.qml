// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// CalendarPickerTodayButton - Built-in today shortcut 内置今天快捷按钮
// Only instantiated while the calendar opts in through showTodayButton.
// 仅在日历通过 showTodayButton 显式开启时创建。
Item {
    id: todayButton

    // ==================== Required Props 必需属性 ====================
    required property var calendarControl

    // ==================== Readonly State 只读状态 ====================
    // Touch has no hover preview: on touch the hover treatment follows the press
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
    readonly property bool _touchActive:
        Touch.feedback(todayArea.containsMouse, todayArea.pressed)

    implicitWidth: todayLabel.implicitWidth + Enums.spacing.l
    implicitHeight: Enums.controlSize.calendarCellHeight

    // ==================== Content 内容 ====================
    Rectangle {
        anchors.fill: parent
        radius: Enums.radius.small
        color: todayButton._touchActive
            ? Enums.stateColor.calendarNavHover : Enums.transparent
    }

    Label {
        id: todayLabel
        anchors.centerIn: parent
        type: Enums.label.type_caption
        text: {
            Translator._v
            return Translator.tr("today")
        }
    }

    MouseArea {
        id: todayArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: todayButton.calendarControl.goToToday()
    }
}
