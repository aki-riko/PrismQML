// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../icons"
import "../data"
import "../feedback/Tooltip"

// Action - Menu action item 菜单动作项
// Supports text position: side (default) or bottom 支持文本位置：侧边（默认）或底部
Rectangle {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string text: ""
    property string icon: ""
    property string shortcut: ""
    property bool checkable: false
    property bool checked: false
    property int textPosition: Enums.position.side  // side or bottom 侧边或底部
    property string actionId: ""         // Unique ID for targeting 唯一标识符
    property string toolTip: ""          // Hover tooltip 悬停提示
    property bool hasSubmenu: false       // Show submenu arrow 显示子菜单箭头
    
    signal triggered()
    signal clicked()  // Alias for triggered 兼容别名
    signal submenuRequested()  // Submenu open request 子菜单打开请求
    readonly property bool hovered: itemArea.containsMouse
    
    // ==================== Size 尺寸 ====================
    width: parent ? parent.width : implicitWidth
    implicitWidth: _isBottomText 
        ? Math.max(Enums.controlSize.menuMinWidth, bottomContent.implicitWidth + Enums.spacing.xl * 2)
        : Math.max(Enums.controlSize.menuMinWidth, sideContent.implicitWidth + Enums.spacing.navBarHeight)
    implicitHeight: _isBottomText 
        ? (Enums.iconSize.xxl + Enums.typography.bodySmall + Enums.spacing.m * 3)
        : Enums.controlSize.emptyStateButtonHeight
    height: implicitHeight
    radius: Enums.radius.small
    
    // ==================== Internal 内部属性 ====================
    readonly property bool _isBottomText: textPosition === Enums.position.bottom
    
    // ==================== Background 背景 ====================
    // 使用 menuItem* token (与 MenuDelegate/ComboBox 一致), controlBgHover 在白底菜单
    // 上视觉过弱 (#fafafa vs 白底, 仅 2% 差) 几乎看不到 hover 反馈。
    color: {
        if (!enabled) return Enums.transparent
        if (itemArea.pressed) return Enums.stateColor.menuItemPressed
        if (checkable && checked) return Enums.stateColor.menuItemPressed
        if (hovered) return Enums.stateColor.menuItemHover
        return Enums.transparent
    }
    
    // ==================== Side Layout (Default) 侧边布局 ====================
    Row {
        id: sideContent
        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.l
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.spacing.l
        visible: !control._isBottomText
        
        // Check mark 选中标记
        Icon {
            iconSize: Enums.iconSize.xs
            color: Enums.accentColor
            width: Enums.spacing.xl
            anchors.verticalCenter: parent.verticalCenter
            visible: control.checkable && control.checked
            icon: Enums.icon.checkmark
        }
        
        // Icon 图标
        Icon {
            iconSize: Enums.iconSize.m
            anchors.verticalCenter: parent.verticalCenter
            visible: control.icon !== ""
            icon: control.icon
        }
        
        // Text 文字
        Label {
            type: Enums.label.type_caption
            text: control.text
            color: control.enabled ? Enums.textColor.primary : Enums.textColor.disabled
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    
    // ==================== Bottom Layout 底部布局 ====================
    Column {
        id: bottomContent
        anchors.centerIn: parent
        spacing: Enums.spacing.xs
        visible: control._isBottomText
        
        // Icon 图标
        Icon {
            iconSize: Enums.iconSize.xxl
            anchors.horizontalCenter: parent.horizontalCenter
            visible: control.icon !== ""
            icon: control.icon
        }
        
        // Text 文字
        Label {
            type: Enums.label.type_caption
            text: control.text
            color: control.enabled ? Enums.textColor.primary : Enums.textColor.disabled
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }
    
    // ==================== Shortcut 快捷键 ====================
    Label {
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.l
        anchors.verticalCenter: parent.verticalCenter
        type: Enums.label.type_caption
        text: control.shortcut
        font.pixelSize: Enums.typography.caption - 1
        color: Enums.stateColor.textMedium
        visible: control.shortcut !== "" && !control._isBottomText && !control.hasSubmenu
    }
    
    // ==================== Submenu Arrow 子菜单箭头 ====================
    Icon {
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.l
        anchors.verticalCenter: parent.verticalCenter
        iconSize: Enums.iconSize.xs
        icon: Enums.icon.chevron_right
        color: control.enabled ? Enums.textColor.secondary : Enums.textColor.disabled
        visible: control.hasSubmenu && !control._isBottomText
    }
    
    // ==================== ToolTip 提示 ====================
    TooltipCore {
        id: tipPopup
        text: control.toolTip
        x: itemArea.mouseX + Enums.spacing.m
        y: control.height + Enums.spacing.xxs
    }
    
    Timer {
        id: tipTimer
        interval: 600
        running: control.toolTip !== "" && itemArea.containsMouse
        onTriggered: tipPopup.show()
    }
    
    Connections {
        target: itemArea
        function onContainsMouseChanged() {
            if (!itemArea.containsMouse) {
                tipTimer.stop()
                tipPopup.hide()
            }
        }
    }
    
    // ==================== Mouse Area 鼠标区域 ====================
    MouseArea {
        id: itemArea
        anchors.fill: parent
        hoverEnabled: true
        enabled: control.enabled
        cursorShape: Qt.ArrowCursor
        onClicked: {
            if (control.hasSubmenu) {
                control.submenuRequested()
                return
            }
            if (control.checkable) control.checked = !control.checked
            control.triggered()
            control.clicked()
        }
    }
}
