// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."       // → qml/ (FluentEnums)
import "../../../icons"    // → controls/icons/
import "../../../../effects"  // → qml/effects/

// CommandBarSurface - Card style command bar 卡片样式命令栏
// Features 特性: shadow, rounded corners, auto-fit width/height 阴影、圆角、自适应宽高
ShadowedRectangle {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var primaryCommands: []
    property var secondaryCommands: []
    property int iconSize: Enums.iconSize.l
    property int buttonStyle: Enums.commandBar.style_icon_only
    property bool tight: true
    property int spacing: Enums.spacing.xs
    property bool showLabels: false  // Show text labels under icons 显示图标下方文字
    
    // ==================== Signals 信号 ====================
    signal actionTriggered(int index, var action)
    signal secondaryActionTriggered(int index, var action)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: innerBar.implicitWidth + Enums.spacing.s * 2
    implicitHeight: innerBar.implicitHeight + Enums.spacing.s * 2
    
    // ==================== Style 样式 ====================
    radius: Enums.radius.large
    color: Enums.cardColor
    border.width: Enums.border.thin
    border.color: Enums.stateColor.border
    
    // ==================== Shadow 阴影 ====================
    shadowLevel: Enums.shadow.level8
    
    // ==================== Inner CommandBar 内部命令栏 ====================
    CommandBarCore {
        id: innerBar
        anchors.centerIn: parent
        // Use parent width minus padding for overflow calculation 使用父宽度减去边距进行溢出计算
        // This ensures buttons are visible while overflow still works 确保按钮可见同时溢出功能正常
        width: Math.max(implicitWidth, control.width - Enums.spacing.s * 2)
        
        primaryCommands: control.primaryCommands
        secondaryCommands: control.secondaryCommands
        iconSize: control.iconSize
        buttonStyle: control.showLabels ? Enums.commandBar.style_text_under : control.buttonStyle
        tight: control.tight
        spacing: control.spacing
        
        onActionTriggered: (index, action) => control.actionTriggered(index, action)
        onSecondaryActionTriggered: (index, action) => control.secondaryActionTriggered(index, action)
    }
}
