// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../icons"
import "../inputs/Toggle"
import "../data"

// TreeMenuDelegate - Tree menu item delegate 树形菜单项委托
// Used by ComboBoxTree, ComboBoxMultiTree 用于树状下拉框
Item {
    id: delegateRoot
    
    // ==================== Props 属性 ====================
    property string text: ""
    property int depth: 0                    // Indentation level 缩进层级
    property bool hasChildren: false         // Has child nodes 是否有子节点
    property bool expanded: false            // Is expanded 是否展开
    property bool checkable: false           // Show checkbox 显示复选框
    property int checkState: 0               // 0=Unchecked, 1=Partial, 2=Checked
    property bool itemEnabled: true
    
    // ==================== Signals 信号 ====================
    signal clicked()
    signal toggleExpand()
    signal checkToggled()
    
    // ==================== State 状态 ====================
    readonly property bool hovered: delegateMouseArea.containsMouse || expandMouseArea.containsMouse
    readonly property bool pressed: delegateMouseArea.pressed
    
    // ==================== Size 尺寸 ====================
    width: parent ? parent.width : Enums.comboBoxMetrics.defaultWidth
    height: Enums.comboBoxMetrics.itemHeight
    
    // ==================== Item Background 项目背景 ====================
    Rectangle {
        id: itemBg
        anchors.fill: parent
        radius: Enums.radius.small
        color: {
            if (!delegateRoot.itemEnabled) return Enums.transparent
            if (delegateRoot.pressed) return Enums.stateColor.menuItemPressed
            if (delegateRoot.hovered) return Enums.stateColor.menuItemHover
            return Enums.transparent
        }
    }
    
    // ==================== Content Row 内容行 ====================
    Row {
        id: contentRow
        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.m + delegateRoot.depth * Enums.spacing.xxl
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.spacing.s
        
        // Expand icon 展开图标
        Item {
            id: expandIconArea
            width: Enums.controlSize.treeIndentSize
            height: Enums.controlSize.treeIndentSize
            anchors.verticalCenter: parent.verticalCenter
            visible: delegateRoot.hasChildren
            
            Icon {
                anchors.centerIn: parent
                icon: Enums.icon.chevron_right
                iconSize: Enums.controlSize.chevronIconSize
                color: Enums.textColor.secondary
                rotation: delegateRoot.expanded ? 90 : 0
                Behavior on rotation { 
                    NumberAnimation { 
                        duration: Enums.duration.fast
                        easing.type: Easing.OutCubic 
                    } 
                }
            }
        }
        
        // Spacer for leaf nodes 叶子节点占位
        Item {
            width: Enums.controlSize.treeIndentSize
            height: Enums.controlSize.treeIndentSize
            visible: !delegateRoot.hasChildren
        }
        
        // Checkbox indicator 复选框指示器
        CheckIndicator {
            anchors.verticalCenter: parent.verticalCenter
            checkState: delegateRoot.checkState
            enabled: delegateRoot.itemEnabled
            hovered: delegateRoot.hovered
            pressed: delegateRoot.pressed
            visible: delegateRoot.checkable
        }
        
        // Text 文本
        Label {
            type: Enums.label.type_body
            text: delegateRoot.text
            color: delegateRoot.hasChildren ? Enums.textColor.secondary : Enums.textColor.primary
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    
    // ==================== Main Interaction 主交互 ====================
    // NOTE: Must be declared BEFORE expandMouseArea so it has lower z-order 注意：必须在 expandMouseArea 之前声明，使得 z 轴更低

    MouseArea {
        id: delegateMouseArea
        anchors.fill: parent
        hoverEnabled: true
        enabled: delegateRoot.itemEnabled
        onClicked: {
            // Checkable mode: toggle check (expand handled by expandMouseArea) 可选择模式：切换选中（展开由 expandMouseArea 处理）

            if (delegateRoot.checkable) {
                delegateRoot.checkToggled()
            } else if (delegateRoot.hasChildren) {
                // Non-checkable with children: toggle expand 非可选中有子节点：切换展开

                delegateRoot.toggleExpand()
            } else {
                // Leaf node without checkbox: clicked 叶子节点无复选框：点击

                delegateRoot.clicked()
            }
        }
    }
    
    // ==================== Expand Click Area (absolute positioned, higher z-order) 展开点击区域（绝对定位，z 轴更高） ====================

    // NOTE: Declared AFTER delegateMouseArea so it has higher z-order 注意：在 delegateMouseArea 之后声明，z 轴更高，优先接收点击

    MouseArea {
        id: expandMouseArea
        x: contentRow.x
        y: (parent.height - height) / 2
        width: Enums.controlSize.treeIndentSize + Enums.spacing.xs * 2
        height: Enums.controlSize.treeIndentSize + Enums.spacing.xs * 2
        visible: delegateRoot.hasChildren && delegateRoot.checkable
        hoverEnabled: true
        onClicked: delegateRoot.toggleExpand()
    }
}
