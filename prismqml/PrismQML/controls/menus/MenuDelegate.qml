// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../icons"
import "../data"
import "../containers"

// MenuDelegate - Unified menu item delegate 统一菜单项委托
// Used by ComboBox, ButtonDropdown, Menu 用于ComboBox、下拉按钮、菜单
Item {
    id: delegateRoot
    
    // ==================== Props 属性 ====================
    property string text: ""
    property string icon: ""
    property bool selected: false
    property bool isSeparator: false
    property bool itemEnabled: true
    
    // ==================== Signals 信号 ====================
    signal clicked()
    
    // ==================== Size 尺寸 ====================
    width: parent ? parent.width : Enums.comboBoxMetrics.defaultWidth
    height: isSeparator ? Enums.controlSize.menuSeparatorHeight : Enums.comboBoxMetrics.itemHeight
    
    // ==================== Separator 分隔线 ====================
    Separator {
        anchors.centerIn: parent
        width: parent.width - Enums.spacing.m * 2
        visible: delegateRoot.isSeparator
    }
    
    // ==================== Item Background 项目背景 ====================
    Rectangle {
        id: itemBg
        anchors.fill: parent
        anchors.leftMargin: Enums.spacing.xs
        anchors.rightMargin: Enums.spacing.xs
        anchors.topMargin: Enums.spacing.xxs
        anchors.bottomMargin: Enums.spacing.xxs
        radius: Enums.radius.small
        visible: !delegateRoot.isSeparator
        
        color: {
            if (!delegateRoot.itemEnabled) return Enums.transparent
            if (delegateMouseArea.pressed) return Enums.stateColor.menuItemPressed
            if (delegateRoot.selected) return Enums.stateColor.menuItemPressed
            if (delegateMouseArea.containsMouse) return Enums.stateColor.menuItemHover
            return Enums.transparent
        }
        
        // ==================== Selection Indicator 选中指示器 ====================
        Rectangle {
            anchors.left: parent.left
            anchors.leftMargin: Enums.spacing.xxs
            anchors.verticalCenter: parent.verticalCenter
            width: Enums.controlSize.topNavIndicatorHeight
            height: Enums.spacing.xl
            radius: Enums.radius.micro
            color: Enums.accentColor
            visible: delegateRoot.selected
        }
        
        // ==================== Item Icon 项目图标 ====================
        Icon {
            id: itemIcon
            anchors.left: parent.left
            anchors.leftMargin: Enums.spacing.l
            anchors.verticalCenter: parent.verticalCenter
            iconSize: Enums.iconSize.m
            icon: delegateRoot.icon
            visible: delegateRoot.icon !== ""
        }
        
        // ==================== Item Text 项目文本 ====================
        Label {
            anchors.left: parent.left
            // Shift text right when icon is present 有图标时文本右移
            anchors.leftMargin: delegateRoot.icon !== "" ? (Enums.spacing.l + Enums.iconSize.m + Enums.spacing.m) : Enums.spacing.l
            anchors.right: parent.right
            anchors.rightMargin: Enums.spacing.l
            anchors.verticalCenter: parent.verticalCenter
            type: Enums.label.type_body
            text: delegateRoot.text
            color: delegateRoot.itemEnabled ? Enums.textColor.primary : Enums.textColor.disabled
            wrapMode: Text.NoWrap  // Override body default WordWrap 覆盖body默认的自动换行
            maximumLineCount: 1    // Single line only 仅单行
            elide: Text.ElideRight
        }
    }
    
    // ==================== Interaction 交互 ====================
    MouseArea {
        id: delegateMouseArea
        anchors.fill: parent
        hoverEnabled: true
        enabled: !delegateRoot.isSeparator && delegateRoot.itemEnabled
        onClicked: delegateRoot.clicked()
    }
}
