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

// TabBar - Standalone Fluent tab navigation bar 独立 Fluent 标签导航栏
// The component owns tab rendering only; page content belongs to TabWidget.
// 组件只负责标签渲染，页面内容由 TabWidget 独立承载。
pragma ComponentBehavior: Bound
Widget {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var tabs: []  // [{title, icon, content?}] or simple strings
    property int currentIndex: 0
    property bool closable: false
    property bool shadowEnabled: true
    property bool movable: false  // Whether tabs can be reordered 是否可重排标签
    property bool scrollable: false  // Reserved compatibility flag 兼容保留属性
    property bool showAddButton: false  // Show add button 显示添加按钮
    property bool detailsEnabled: false  // Show subtitle/badge rows 显示副标题和状态
    property bool contextMenuEnabled: false  // Report tab right-clicks 报告标签右键请求
    property int tabBarHeight: Enums.controlSize.tableHeaderHeight
    property int tabContentVerticalPadding: Enums.spacing.xs  // Vertical breathing room around detailed tab content 详细标签内容上下留白
    property int tabWidth: 0  // Fixed width; zero keeps content sizing 固定宽度，零值按内容计算
    property int minimumTabWidth: Enums.controlSize.segmentedMinWidth
    property int maximumTabWidth: 0  // Zero means unlimited 零值表示不限制
    property bool interactionEnabled: true
    property var canCloseTab: null  // Optional function(index, tab)->bool 可选关闭判定

    readonly property var _safeTabs:
        tabs === null || tabs === undefined ? []
        : (typeof tabs.length === "number" ? tabs : [])

    // ==================== Internal Props 内部属性 ====================
    readonly property int _tabHeight: detailsEnabled
        ? Math.max(
            Enums.controlSize.inputHeightLarge - Enums.spacing.xs,
            _tabBarHeight - Math.max(0, tabContentVerticalPadding) * 2)
        : Enums.controlSize.inputHeightLarge - Enums.spacing.xs
    readonly property int _tabBarHeight: Math.max(
        Enums.controlSize.tableHeaderHeight, tabBarHeight)
    readonly property int _selectedTabRadius: Enums.surfaceRadius(Enums.radius.card)
    readonly property real _selectedTabBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property real _availableWidth: control.width - Enums.spacing.xs * 2 - (control.showAddButton ? Enums.controlSize.segmentedHeight : 0)
    property int _dragSourceIndex: -1
    property int _dragVisualIndex: -1
    property real _dragSourceOffsetX: 0
    property real _dragPointerRowX: 0
    readonly property bool _dragging: _dragSourceIndex >= 0

    // Add button is exposed for popup anchoring without exposing implementation ids.
    // 对外暴露添加按钮供弹层锚定，但不暴露内部实现对象。
    readonly property alias addButtonItem: addButton

    // ==================== Signals 信号 ====================
    signal currentChanged(int index)  // Current tab changed 当前标签改变
    signal tabClicked(int index)  // Tab clicked 标签点击
    signal tabClosed(int index)  // Tab close requested 标签关闭请求
    signal tabAddClicked()  // Add button clicked 添加按钮点击
    signal tabDoubleClicked(int index)  // Tab double clicked 标签双击
    signal tabContextMenuRequested(int index, point position)  // Tab context menu request 标签上下文菜单请求
    signal tabsReordered(int from, int to)  // Tabs reordered via drag 拖拽重排

    // ==================== Public Methods 公开方法 ====================
    function addTab(title, icon, content) {
        var newTabs = (_safeTabs || []).slice()
        newTabs.push({title: title, icon: icon || "", content: content})
        tabs = newTabs
        return newTabs.length - 1
    }

    function insertTab(index, title, icon, content) {
        var newTabs = (_safeTabs || []).slice()
        var idx = Math.max(0, Math.min(index, newTabs.length))
        newTabs.splice(idx, 0, {title: title, icon: icon || "", content: content})
        tabs = newTabs
        return idx
    }

    function removeTab(index) {
        if (index < 0 || index >= (_safeTabs || []).length) return
        var newTabs = (_safeTabs || []).slice()
        newTabs.splice(index, 1)
        tabs = newTabs
        if (currentIndex >= newTabs.length)
            currentIndex = Math.max(0, newTabs.length - 1)
    }

    function clear() {
        tabs = []
        currentIndex = 0
    }

    function count() { return (_safeTabs || []).length }

    function tabText(index) {
        if (index < 0 || index >= (_safeTabs || []).length) return ""
        var tab = (_safeTabs || [])[index]
        return tab && typeof tab === "object" ? (tab.title || "") : String(tab || "")
    }

    function setTabText(index, text) {
        if (index < 0 || index >= (_safeTabs || []).length) return
        var newTabs = (_safeTabs || []).slice()
        var current = newTabs[index]
        newTabs[index] = typeof current === "object"
            ? Object.assign({}, current, {title: text})
            : {title: text}
        tabs = newTabs
    }

    function tabIcon(index) {
        if (index < 0 || index >= (_safeTabs || []).length) return ""
        var tab = (_safeTabs || [])[index]
        return tab && typeof tab === "object" ? (tab.icon || "") : ""
    }

    function setTabIcon(index, icon) {
        if (index < 0 || index >= (_safeTabs || []).length) return
        var newTabs = (_safeTabs || []).slice()
        var current = newTabs[index]
        newTabs[index] = typeof current === "object"
            ? Object.assign({}, current, {icon: icon})
            : {title: String(current || ""), icon: icon}
        tabs = newTabs
    }

    function setCurrentIndex(index) {
        if (index >= 0 && index < (_safeTabs || []).length)
            currentIndex = index
    }

    function tabsClosable() { return closable }

    function tabCloseEnabled(index, tab) {
        return !canCloseTab || canCloseTab(index, tab) !== false
    }

    // ==================== Size 尺寸 ====================
    contentWidth: Enums.controlSize.chartDefaultWidth
    contentHeight: _tabBarHeight

    onCurrentIndexChanged: {
        currentChanged(currentIndex)
        if (tabFlickable) tabFlickable.scrollToCurrentTab()
        if (slidingIndicator) slidingIndicator._scheduleSync(true)
    }

    // ==================== Content 内容 ====================
    TabEdgeAutoScroll {
        id: _edgeAutoScrollTimer
        host: control
        tabFlickable: tabFlickable
        running: control._dragging
    }

    Rectangle {
        id: tabBarBg
        objectName: "tabBarBg"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: control._tabBarHeight
        color: Enums.stateColor.cardDefaultBg
        clip: true

        TabIndicator {
            id: slidingIndicator
            host: control
            tabBar: tabBarBg
            tabFlickable: tabFlickable
            tabRepeater: tabRepeater
            tabRow: tabRow
        }
    }

    Flickable {
        id: tabFlickable

        function smoothScrollTo(targetX) { tabScrollHelper.scrollTo(targetX) }
        function smoothScrollBy(delta) { tabScrollHelper.scrollBy(delta) }

        function scrollToCurrentTab() {
            if (control.currentIndex < 0 || control.currentIndex >= tabRepeater.count) return
            var item = tabRepeater.itemAt(control.currentIndex)
            if (!item) return
            var itemLeft = item.x
            var itemRight = item.x + item.width
            if (itemLeft < tabScrollHelper.targetPos)
                smoothScrollTo(itemLeft)
            else if (itemRight > tabScrollHelper.targetPos + width)
                smoothScrollTo(itemRight - width)
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

        SmoothScrollHelper {
            id: tabScrollHelper
            target: tabFlickable
            orientation: Qt.Horizontal
            enabled: true
            bounceEnabled: true
            // Keep the historical TabWidget behavior: wheel input remains active
            // even when callers leave the compatibility property at its default.
            // 保持旧 TabWidget 行为：即使调用方使用默认值，滚轮仍可用。
            handleWheel: true
        }

        Row {
            id: tabRow
            height: control._tabHeight
            spacing: Enums.spacing.none

            Repeater {
                id: tabRepeater
                model: control._safeTabs

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

    Rectangle {
        id: addButton
        objectName: "tabBarAddButton"
        width: Enums.controlSize.closeButtonSize
        height: Enums.controlSize.closeButtonSize
        radius: width / 2
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
            enabled: control.interactionEnabled
        }

        TapHandler {
            enabled: control.interactionEnabled
            onTapped: control.tabAddClicked()
        }
    }
}
