// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../icons"

// CalendarNavButton - Navigation button for CalendarPickerCore 日历导航按钮
// Extracted from CalendarPickerCore for modularity 从CalendarPickerCore提取以模块化
Rectangle {
    id: navBtn
    
    // ==================== Props 属性 ====================
    property string icon: Enums.icon.chevron_up
    
    signal clicked()
    
    width: 32
    height: 34
    radius: Enums.radius.small
    color: navArea.pressed 
        ? Enums.stateColor.calendarNavPressed
        : (navArea.containsMouse 
            ? Enums.stateColor.calendarNavHover
            : Enums.transparent)
    
    Icon {
        anchors.centerIn: parent
        iconSize: Enums.iconSize.s
        icon: navBtn.icon
        color: Enums.isDark ? Enums.calendarColors.navIconDark : Enums.calendarColors.navIconLight
    }
    
    MouseArea {
        id: navArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: navBtn.clicked()
    }
}
