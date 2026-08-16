// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../icons"
import "../buttons"
import "../../effects"
import "../data"
import "../containers/ScrollBar"
import "../containers"
import "_internal"
import QtQuick.Effects

// TabWidget - Fluent Design style tab widget 标签页组件
Widget {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var tabs: []  // [{title, icon, content: Component}]
    property int currentIndex: 0
    property bool closable: false
    property bool shadowEnabled: true
    property bool movable: false  // Whether tabs can be reordered 是否可拖拽排序
    property bool scrollable: false  // Whether tab bar is scrollable 是否可滚动
    property bool showAddButton: false  // Show add button 显示添加按钮

    readonly property var _safeTabs:
        tabs === null || tabs === undefined ? []
        : (typeof tabs.length === "number" ? tabs : [])

    // ==================== Internal Props 内部属性 ====================
    readonly property int _tabHeight: Enums.controlSize.inputHeightLarge - Enums.spacing.xs
    readonly property int _tabBarHeight: Enums.controlSize.tableHeaderHeight
    readonly property int _selectedTabRadius: Enums.surfaceRadius(Enums.radius.card)
    readonly property real _selectedTabBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property real _availableWidth: control.width - Enums.spacing.xs * 2 - (control.showAddButton ? Enums.controlSize.segmentedHeight : 0)
    property int _dragSourceIndex: -1
    property int _dragVisualIndex: -1
    property real _dragSourceOffsetX: 0
    property real _dragPointerRowX: 0
    readonly property bool _dragging: _dragSourceIndex >= 0
    
    // ==================== Signals 信号 ====================
    signal currentChanged(int index)  // Current tab changed 当前标签改变
    signal tabClicked(int index)  // Tab clicked 标签点击
    signal tabClosed(int index)  // Tab close requested 标签关闭请求
    signal tabAddClicked()  // Add button clicked 添加按钮点击
    signal tabDoubleClicked(int index)  // Tab double clicked 标签双击
    signal tabsReordered(int from, int to)  // Tabs reordered via drag 拖拽重排
    
    // ==================== Public Methods 公开方法 ====================
    
    // Add a new tab 添加新标签
    function addTab(title, icon, content) {
        var newTabs = (_safeTabs || []).slice()
        newTabs.push({title: title, icon: icon || "", content: content})
        tabs = newTabs
        return newTabs.length - 1
    }
    
    // Insert a tab at index 在指定位置插入标签
    function insertTab(index, title, icon, content) {
        var newTabs = (_safeTabs || []).slice()
        var idx = Math.max(0, Math.min(index, newTabs.length))
        newTabs.splice(idx, 0, {title: title, icon: icon || "", content: content})
        tabs = newTabs
        return idx
    }
    
    // Remove tab at index 移除指定位置的标签
    function removeTab(index) {
        if (index < 0 || index >= (_safeTabs || []).length) return
        var newTabs = (_safeTabs || []).slice()
        newTabs.splice(index, 1)
        tabs = newTabs
        if (currentIndex >= newTabs.length) {
            currentIndex = Math.max(0, newTabs.length - 1)
        }
    }
    
    // Clear all tabs 清空所有标签
    function clear() {
        tabs = []
        currentIndex = 0
    }
    
    // Get tab count 获取标签数量
    function count() {
        return (_safeTabs || []).length
    }
    
    // Get tab text 获取标签文本
    function tabText(index) {
        if (index < 0 || index >= (_safeTabs || []).length) return ""
        var tab = (_safeTabs || [])[index]
        return tab ? (tab.title || "") : ""
    }
    
    // Set tab text 设置标签文本
    function setTabText(index, text) {
        if (index < 0 || index >= (_safeTabs || []).length) return
        var newTabs = (_safeTabs || []).slice()
        newTabs[index] = Object.assign({}, newTabs[index] || {}, {title: text})
        tabs = newTabs
    }
    
    // Get tab icon 获取标签图标
    function tabIcon(index) {
        if (index < 0 || index >= (_safeTabs || []).length) return ""
        var tab = (_safeTabs || [])[index]
        return tab ? (tab.icon || "") : ""
    }
    
    // Set tab icon 设置标签图标
    function setTabIcon(index, icon) {
        if (index < 0 || index >= (_safeTabs || []).length) return
        var newTabs = (_safeTabs || []).slice()
        newTabs[index] = Object.assign({}, newTabs[index] || {}, {icon: icon})
        tabs = newTabs
    }
    
    // Set current index 设置当前索引
    function setCurrentIndex(index) {
        if (index >= 0 && index < (_safeTabs || []).length) {
            currentIndex = index
        }
    }
    
    
    // Check if tabs are closable 检查标签是否可关闭
    function tabsClosable() {
        return closable
    }

    // ==================== Size 尺寸 ====================
    // Content size (inherited from Widget) 内容尺寸（继承自Widget）
    contentWidth: Enums.controlSize.chartDefaultWidth
    contentHeight: Enums.controlSize.chartDefaultHeight

    // Emit currentChanged and reveal the selected tab 当前索引变化时发信号并显示选中标签
    onCurrentIndexChanged: {
        currentChanged(currentIndex)
        if (tabFlickable) tabFlickable.scrollToCurrentTab()
        if (slidingIndicator) slidingIndicator._scheduleSync(true)
    }

    // ==================== Content 内容 ====================
    // Drag edge auto-scroll follows the display refresh rate.
    // 拖拽边缘自动滚动跟随屏幕刷新率。
    TabEdgeAutoScroll {
        id: _edgeAutoScrollTimer
        host: control
        tabFlickable: tabFlickable
        running: control._dragging
    }
    
    // Tab bar background with clip 标签栏背景（带裁剪）
    Rectangle {
        id: tabBarBg
        objectName: "tabBarBg"  // For SmoothScrollHelper detection 用于SmoothScrollHelper检测
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: control._tabBarHeight
        color: Enums.stateColor.cardDefaultBg
        clip: true  // Clip sliding indicators 裁剪滑动指示器
        
        // Sliding indicator 滑动指示器
        // Fluent Design: selected tab has subtle border and shadow 选中标签有精细边框和微妙阴影

        TabIndicator {
            id: slidingIndicator
            host: control
            tabBar: tabBarBg
            tabFlickable: tabFlickable
            tabRepeater: tabRepeater
            tabRow: tabRow
        }
    }
    
    // Tab items container 标签项容器（可滚动）
    Flickable {
        id: tabFlickable

        // Smooth scroll methods delegated to the helper 平滑滚动方法委托给helper
        function smoothScrollTo(targetX) { tabScrollHelper.scrollTo(targetX) }
        function smoothScrollBy(delta) { tabScrollHelper.scrollBy(delta) }

        // Scroll to current selected tab 滚动到当前选中标签
        function scrollToCurrentTab() {
            if (control.currentIndex < 0 || control.currentIndex >= tabRepeater.count) return
            var item = tabRepeater.itemAt(control.currentIndex)
            if (!item) return

            var itemLeft = item.x
            var itemRight = item.x + item.width

            if (itemLeft < tabScrollHelper.targetPos) {
                smoothScrollTo(itemLeft)
            }
            else if (itemRight > tabScrollHelper.targetPos + width) {
                smoothScrollTo(itemRight - width)
            }
        }

        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.xs
        anchors.bottom: tabBarBg.bottom
        anchors.bottomMargin: (tabBarBg.height - control._tabHeight) / 2
        width: Math.min(tabRow.width, control._availableWidth)
        height: control._tabHeight
        contentWidth: tabRow.width
        contentHeight: control._tabHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        z: Enums.zIndex.header
        
        // Smooth scroll helper 平滑滚动助手
        SmoothScrollHelper {
            id: tabScrollHelper
            target: tabFlickable
            orientation: Qt.Horizontal
            enabled: true
            bounceEnabled: true
            handleWheel: true
        }
        
        Row {
            id: tabRow
            height: control._tabHeight
            spacing: Enums.spacing.none
            
            Repeater {
                id: tabRepeater
                model: control._safeTabs

                // delegate 创建/销毁时刷新 currentTab (itemAt 非响应式, 必须显式触发)
                onItemAdded: slidingIndicator._currentTabKey++
                onItemRemoved: slidingIndicator._currentTabKey++

                TabItem {
                    host: control
                    rowContainer: tabRow
                    repeater: tabRepeater
                }
            }
        }
    }
        
    // Add button 添加按钮
    Rectangle {
        id: addButton
        width: Enums.controlSize.closeButtonSize
        height: Enums.controlSize.closeButtonSize
        radius: width / 2  // Circle 圆形
        visible: control.showAddButton
        anchors.left: tabFlickable.right
        anchors.leftMargin: Enums.spacing.xs
        anchors.bottom: tabBarBg.bottom
        anchors.bottomMargin: (control._tabBarHeight - Enums.controlSize.closeButtonSize) / 2
        z: Enums.zIndex.controls
        color: addHoverHandler.hovered ? Enums.stateColor.hover : Enums.transparent
        
        Icon {
            anchors.centerIn: parent
            iconSize: Enums.iconSize.xs
            color: Enums.secondaryForeground
            icon: Enums.icon.add
        }
        
        HoverHandler {
            id: addHoverHandler
            cursorShape: Qt.PointingHandCursor
        }
        
        TapHandler {
            onTapped: control.tabAddClicked()
        }
    }
    
    // Content area 内容区
    TabContentPages {
        id: tabContentPages
        anchors.top: tabBarBg.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        host: control
    }
}
