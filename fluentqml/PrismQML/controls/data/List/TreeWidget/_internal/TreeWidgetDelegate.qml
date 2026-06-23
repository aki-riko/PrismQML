// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../../../../.."
import "../../../../icons"
import "../../../../inputs/Toggle"
import "../../../../data"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// TreeWidgetDelegate - Tree item delegate 树形项委托
// Internal module for TreeWidget 树形组件内部模块
// Uses ListView.view to access parent ListView and control 使用 ListView.view 访问父级

Rectangle {
    id: delegateRoot
    required property int index
    required property var model
    
    // Access control via ListView.view.treeControl 通过 ListView.view.treeControl 访问控制器
    readonly property var control: ListView.view ? ListView.view.treeControl : null
    readonly property ListView listView: ListView.view
    
    // Extract from model 从模型提取
    property string itemText: model.text || ""
    property string itemIcon: model.icon || ""
    property int depth: model.depth || 0
    property bool hasChildren: model.hasChildren || false
    property bool expanded: model.expanded || false
    property bool itemCheckable: model.checkable || false
    property int checkState: model.checkState || 0
    property string pathStr: model.pathStr || ""
    property var itemData: model.data || ({})
    
    width: listView ? listView.width : 0
    height: control ? control.itemHeight : Enums.controlSize.treeItemHeight
    color: Enums.transparent

    property bool selected: control && control.currentIndex >= 0 && control._isIndexSelected(index)
    property bool hovered: control && control._hoverIndex === index
    property bool pressed: itemArea.pressed
    property real branchOffset: Enums.spacing.m + depth * (control ? control.indentWidth : Enums.spacing.xl)

    // Press scale 按压缩放
    scale: pressed ? 0.98 : 1.0
    Behavior on scale {
        NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic }
    }
    transformOrigin: Item.Center

    // Background 背景
    Rectangle {
        anchors.fill: parent
        anchors.margins: Enums.spacing.xxs
        radius: Enums.radius.small
        // 状态色合成成不透明 (Qt.tint 到 cardColor), 在不透明色之间插值才平滑;
        // 否则透明黑 -> 半透明灰的 ColorAnimation 中间帧会闪过脏灰 (灰块跳变)
        color: {
            if (delegateRoot.selected || delegateRoot.hovered)
                return Qt.tint(Enums.cardColor, Enums.stateColor.treeItemHover)
            return Enums.cardColor
        }
        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
    }

    // Selection indicator 选中指示条
    Rectangle {
        id: selectionIndicator
        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.xxs
        anchors.verticalCenter: parent.verticalCenter
        width: Enums.border.thick
        height: Math.max(0, parent.height - Enums.controlSize.treeIndicatorMargin)
        radius: Enums.radius.small
        color: control ? control.indicatorColor : Enums.accentColor

        property bool _active: control && control.currentIndex >= 0 && control.currentIndex === delegateRoot.index
        opacity: _active ? 1 : 0
        scale: _active ? 1 : 0
        transformOrigin: Item.Center

        Behavior on opacity {
            NumberAnimation { duration: selectionIndicator._active ? Enums.duration.medium : Enums.duration.fast; easing.type: Easing.OutCubic }
        }
        Behavior on scale {
            NumberAnimation { duration: Enums.duration.spring; easing.type: Easing.OutBack }
        }
    }
    
    // Content row 内容行
    Row {
        id: contentRow
        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.xl + delegateRoot.branchOffset
        anchors.verticalCenter: parent.verticalCenter
        spacing: 0
        
        // Expand button 展开按钮
        Item {
            width: Enums.controlSize.treeIndentSize
            height: Enums.controlSize.treeIndentSize
            visible: delegateRoot.hasChildren
            
            Icon {
                anchors.centerIn: parent
                iconSize: Enums.iconSize.tiny
                color: Enums.textColor.secondary
                icon: Enums.icon.chevron_right
                rotation: delegateRoot.expanded ? 90 : 0
                Behavior on rotation { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutBack } }
            }
        }
        
        Item {
            width: Enums.controlSize.treeIndentSize
            height: Enums.controlSize.treeIndentSize
            visible: !delegateRoot.hasChildren
        }
        
        Item { width: Enums.spacing.xs; height: 1 }
        
        // Checkbox 复选框
        CheckIndicator {
            visible: (control && control.checkable) || delegateRoot.itemCheckable
            checkState: delegateRoot.checkState
            enabled: true
            hovered: delegateRoot.hovered
            pressed: itemArea.pressed
            checkedColor: control ? control.indicatorColor : Enums.accentColor
        }
        
        Item { width: ((control && control.checkable) || delegateRoot.itemCheckable) ? Enums.spacing.xs : 0; height: 1 }
        
        // Icon 图标
        Icon {
            iconSize: Enums.controlSize.treeIndentSize
            visible: delegateRoot.itemIcon !== ""
            icon: delegateRoot.itemIcon
            color: Enums.textColor.primary
        }
        
        Item { width: delegateRoot.itemIcon !== "" ? Enums.spacing.s : 0; height: 1 }
        
        // Text 文本
        Label {
            type: Enums.label.type_caption
            text: delegateRoot.itemText
            color: control ? control.textColor : Enums.textColor.primary
            elide: Text.ElideRight
            width: Math.min(implicitWidth, (listView ? listView.width : 200) - contentRow.x - Enums.spacing.xl)
        }
    }
    
    // Mouse area 鼠标区域
    MouseArea {
        id: itemArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        
        property real expandBtnStart: Enums.spacing.xl + delegateRoot.branchOffset - Enums.spacing.xxs
        property real expandBtnEnd: expandBtnStart + Enums.controlSize.treeIndentSize + Enums.spacing.xs
        
        onEntered: {
            if (!control) return
            control._hoverIndex = delegateRoot.index
            control.itemEntered(control._getItemObject(delegateRoot.index), delegateRoot.index)
        }
        onExited: {
            if (!control) return
            if (control._hoverIndex === delegateRoot.index) control._hoverIndex = -1
        }
        onPressed: (mouse) => {
            if (!control) return
            // Skip selection for expand button area 跳过展开按钮区域的选择
            if (delegateRoot.hasChildren && mouse.x >= expandBtnStart && mouse.x <= expandBtnEnd) {
                return
            }
            control.itemPressed(control._getItemObject(delegateRoot.index), delegateRoot.index)
        }
        onClicked: (mouse) => {
            if (!control) return
            if (delegateRoot.hasChildren && mouse.x >= expandBtnStart && mouse.x <= expandBtnEnd) {
                control._toggleExpandAt(delegateRoot.index)
                return
            }
            var checkboxStart = expandBtnEnd + Enums.spacing.xs
            var checkboxEnd = checkboxStart + Enums.controlSize.checkboxOuter
            if ((control.checkable || delegateRoot.itemCheckable) && mouse.x >= checkboxStart && mouse.x <= checkboxEnd) {
                control._toggleCheckAt(delegateRoot.index)
                return
            }
            control._handleItemClick(delegateRoot.index, mouse.button, mouse.modifiers)
            control.itemClicked(control._getItemObject(delegateRoot.index), delegateRoot.index)
        }
        onDoubleClicked: {
            if (!control) return
            control.itemDoubleClicked(control._getItemObject(delegateRoot.index), delegateRoot.index)
            if (delegateRoot.hasChildren) control._toggleExpandAt(delegateRoot.index)
        }
    }
}
