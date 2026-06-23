// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../data/Label"

// FilterBarCore - Filter base class 过滤器基类
// Pill buttons in gray container 药丸按钮在灰色容器中
// Supports: pure text / pure icon / icon+text (auto-detect) 支持纯文本/纯图标/图标+文本（自动识别）
Rectangle {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    // Items format 选项格式:
    //   - String: "All" (text) or "Home" (icon name if PascalCase >3 chars)
    //   - Object: { text: "Home", icon: "Home" } or { text: "Home" } or { icon: "Home" }
    property var items: []
    property int currentIndex: 0  // Current selected index (exclusive mode) 当前选中索引（互斥模式）
    property bool exclusive: true  // true=单选, false=多选
    property var selectedIndices: [0]  // Selected indexes (multi-select mode) 选中索引（多选模式）
    property int iconSize: Enums.iconSize.s  // Icon size for filter items 过滤项图标尺寸
    
    // ==================== Signals 信号 ====================
    signal itemClicked(int index)
    signal selectionChanged(var indices)
    signal indexChanged(int index)  // Renamed to avoid conflict with currentIndex property 重命名避免与属性冲突
    
    // ==================== Size 尺寸 ====================
    implicitWidth: filterRow.implicitWidth + Enums.spacing.m * 2
    implicitHeight: Enums.controlSize.inputHeightLarge  // 40
    radius: Enums.radius.small
    
    // ==================== Color Functions (subclass can override) 颜色函数 ====================
    
    // Container background 容器背景色
    property var getContainerColor: function() {
        return Enums.stateColor.filterContainer
    }
    
    // Item background 选项背景色
    property var getItemBackgroundColor: function(selected, hovered) {
        if (selected) {
            return Enums.accentColor
        }
        if (hovered) {
            return Enums.stateColor.filterItemHover
        }
        return Enums.transparent
    }
    
    // Item text color 选项文字颜色
    property var getItemTextColor: function(selected) {
        if (selected) {
            return Enums.themeColors.accentForeground
        }
        return Enums.textColor.primary
    }
    
    // ==================== Appearance 外观 ====================
    color: getContainerColor()
    opacity: enabled ? 1.0 : 0.5
    
    // ==================== Helper Function 辅助函数 ====================
    
    // Parse item data - auto detect icon/text 解析选项数据 - 自动识别图标/文本
    // Returns: { icon: string, text: string }
    function parseItem(data) {
        // Object format 对象格式
        if (typeof data === "object" && data !== null) {
            return {
                icon: data.icon || "",
                text: data.text || ""
            }
        }
        // String format - auto detect 字符串格式 - 自动识别
        if (typeof data === "string") {
            // Check for icon name (PascalCase, >3 chars) 检查是否为图标名称（PascalCase，>3 字符）
            var isIconName = /^[A-Z][a-zA-Z0-9]+$/.test(data) && data.length > 3
            if (isIconName) {
                return { icon: data, text: "" }
            }
            return { icon: "", text: data }
        }
        return { icon: "", text: String(data) }
    }
    
    // Calculate item position for sliding indicator 计算滑动指示器位置
    function getItemX(idx) {
        if (idx < 0 || idx >= itemRepeater.count) return 0
        var x = 0
        for (var i = 0; i < idx; i++) {
            var item = itemRepeater.itemAt(i)
            if (item) x += item.width + Enums.spacing.xs
        }
        return x
    }
    
    function getItemWidth(idx) {
        if (idx < 0 || idx >= itemRepeater.count) return 0
        var item = itemRepeater.itemAt(idx)
        return item ? item.width : 0
    }

    // ==================== Public Methods 公共方法 ====================

    function getCurrentIndex() { return currentIndex }

    function isEnabled() { return enabled }

    // ==================== Content 内容 ====================
    Item {
        id: contentContainer
        anchors.centerIn: parent
        width: filterRow.implicitWidth
        height: filterRow.implicitHeight
        
        // Sliding indicator for exclusive mode 互斥模式滑动指示器
        Rectangle {
            id: slidingIndicator
            visible: control.exclusive && itemRepeater.count > 0
            
            // Use properties to allow forced refresh 使用属性以允许强制刷新
            property int targetIndex: control.currentIndex
            property int refreshTrigger: 0  // Trigger recalculation 触发重新计算
            
            x: refreshTrigger >= 0 ? control.getItemX(targetIndex) : 0
            width: refreshTrigger >= 0 ? control.getItemWidth(targetIndex) : 0
            height: 30
            radius: Enums.radius.small
            color: Enums.accentColor
            
            // Smooth sliding animation 平滑滑动动画
            Behavior on x { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic } }
            Behavior on width { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic } }
        }
        
        Row {
            id: filterRow
            spacing: Enums.spacing.xs
            
            Repeater {
                id: itemRepeater
                model: control.items
                
                // Refresh indicator after all items are created 所有项创建完成后刷新指示器
                onItemAdded: (index, item) => {
                    // Refresh when current item or any item before it is added (needed for x calculation) 当当前项或其之前的任何项添加时刷新（x 计算需要）
                    if (index <= control.currentIndex) {
                        slidingIndicator.refreshTrigger++
                    }
                }
                
                Rectangle {
                    id: filterItem
                    width: itemContentRow.implicitWidth + Enums.spacing.xl * 2
                    height: 30
                    radius: Enums.radius.small
                    
                    required property int index
                    required property var modelData
                    
                    // Parsed item data 解析后的选项数据
                    readonly property var parsedData: control.parseItem(modelData)
                    readonly property string itemIcon: parsedData.icon
                    readonly property string itemText: parsedData.text
                    readonly property bool hasIcon: itemIcon !== ""
                    readonly property bool hasText: itemText !== ""
                    
                    property bool selected: control.exclusive ? 
                        (index === control.currentIndex) : 
                        (control.selectedIndices.indexOf(index) >= 0)
                    property bool hovered: itemArea.containsMouse && control.enabled
                    property bool pressed: itemArea.pressed
                    
                    // Background: transparent for exclusive (indicator handles it), colored for multi 背景：互斥模式透明（指示器处理），多选模式着色
                    color: control.exclusive ? 
                        (hovered && !selected ? Enums.stateColor.filterItemHover : Enums.transparent) :
                        control.getItemBackgroundColor(selected, hovered)
                    
                    // Scale animation - bounce effect for multi-select 缩放动画 - 多选模式弹性效果
                    scale: pressed ? 0.92 : 1.0
                    transformOrigin: Item.Center
                    
                    // Animations 动画
                    Behavior on color { ColorAnimation { duration: Enums.duration.normal; easing.type: Easing.OutCubic } }
                    Behavior on scale { 
                        NumberAnimation { 
                            duration: control.exclusive ? Enums.duration.fast : Enums.duration.medium
                            easing.type: control.exclusive ? Easing.OutCubic : Easing.OutBack
                            easing.overshoot: 2.5
                        } 
                    }
                    
                    // Content Row (icon + text) 内容行
                    Row {
                        id: itemContentRow
                        anchors.centerIn: parent
                        spacing: filterItem.hasIcon && filterItem.hasText ? Enums.spacing.xs : 0
                        
                        // Icon 图标
                        Icon {
                            icon: filterItem.itemIcon
                            iconSize: control.iconSize
                            color: control.getItemTextColor(filterItem.selected)
                            visible: filterItem.hasIcon
                            anchors.verticalCenter: parent.verticalCenter
                            
                            Behavior on color { ColorAnimation { duration: Enums.duration.normal; easing.type: Easing.OutCubic } }
                        }
                        
                        // Text 文字
                        Label {
                            type: Enums.label.type_body_small
                            text: filterItem.itemText
                            color: control.getItemTextColor(filterItem.selected)
                            visible: filterItem.hasText
                            anchors.verticalCenter: parent.verticalCenter
                            
                            Behavior on color { ColorAnimation { duration: Enums.duration.normal; easing.type: Easing.OutCubic } }
                        }
                    }
                    
                    // Interaction 交互
                    MouseArea {
                        id: itemArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: control.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                        enabled: control.enabled
                        
                        onClicked: {
                            if (control.exclusive) {
                                if (control.currentIndex !== filterItem.index) {
                                    control.currentIndex = filterItem.index
                                    control.indexChanged(filterItem.index)
                                }
                            } else {
                                var idx = control.selectedIndices.indexOf(filterItem.index)
                                var newIndices = control.selectedIndices.slice()
                                if (idx >= 0) {
                                    newIndices.splice(idx, 1)
                                } else {
                                    newIndices.push(filterItem.index)
                                }
                                control.selectedIndices = newIndices
                                control.selectionChanged(newIndices)
                            }
                            control.itemClicked(filterItem.index)
                        }
                    }
                }
            }
        }
    }
}
