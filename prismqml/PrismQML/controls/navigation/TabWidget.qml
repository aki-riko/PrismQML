// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal"

// TabWidget - Fluent tabs with independent page content Fluent 标签与独立页面内容
// TabBar owns tab interaction; TabWidget only composes the page area.
// TabBar 负责标签交互，TabWidget 只组合页面区域。
Widget {
    id: control

    // ==================== Public Props 公开属性 ====================
    property alias tabs: tabBar.tabs
    property alias currentIndex: tabBar.currentIndex
    property alias closable: tabBar.closable
    property alias shadowEnabled: tabBar.shadowEnabled
    property alias movable: tabBar.movable
    property alias scrollable: tabBar.scrollable
    property alias showAddButton: tabBar.showAddButton
    property alias detailsEnabled: tabBar.detailsEnabled
    property alias tabWidth: tabBar.tabWidth
    property alias minimumTabWidth: tabBar.minimumTabWidth
    property alias maximumTabWidth: tabBar.maximumTabWidth
    property alias interactionEnabled: tabBar.interactionEnabled
    property alias canCloseTab: tabBar.canCloseTab

    readonly property alias _safeTabs: tabBar._safeTabs
    readonly property alias _tabHeight: tabBar._tabHeight
    readonly property alias _tabBarHeight: tabBar._tabBarHeight
    readonly property alias _selectedTabRadius: tabBar._selectedTabRadius
    readonly property alias _selectedTabBorderWidth: tabBar._selectedTabBorderWidth
    readonly property alias _dragging: tabBar._dragging
    property alias _dragSourceIndex: tabBar._dragSourceIndex
    property alias _dragVisualIndex: tabBar._dragVisualIndex
    property alias _dragSourceOffsetX: tabBar._dragSourceOffsetX
    property alias _dragPointerRowX: tabBar._dragPointerRowX
    readonly property alias tabBarItem: tabBar

    // ==================== Signals 信号 ====================
    signal currentChanged(int index)
    signal tabClicked(int index)
    signal tabClosed(int index)
    signal tabAddClicked()
    signal tabDoubleClicked(int index)
    signal tabsReordered(int from, int to)

    // ==================== Public Methods 公开方法 ====================
    function addTab(title, icon, content) { return tabBar.addTab(title, icon, content) }
    function insertTab(index, title, icon, content) {
        return tabBar.insertTab(index, title, icon, content)
    }
    function removeTab(index) { tabBar.removeTab(index) }
    function clear() { tabBar.clear() }
    function count() { return tabBar.count() }
    function tabText(index) { return tabBar.tabText(index) }
    function setTabText(index, text) { tabBar.setTabText(index, text) }
    function tabIcon(index) { return tabBar.tabIcon(index) }
    function setTabIcon(index, icon) { tabBar.setTabIcon(index, icon) }
    function setCurrentIndex(index) { tabBar.setCurrentIndex(index) }
    function tabsClosable() { return tabBar.tabsClosable() }

    // ==================== Size 尺寸 ====================
    contentWidth: Enums.controlSize.chartDefaultWidth
    contentHeight: Enums.controlSize.chartDefaultHeight

    onCurrentIndexChanged: currentChanged(currentIndex)

    // ==================== Content 内容 ====================
    TabBar {
        id: tabBar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: _tabBarHeight
    }

    TabContentPages {
        id: tabContentPages
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        host: control
    }

    Connections {
        target: tabBar

        function onTabClicked(index) { control.tabClicked(index) }
        function onTabClosed(index) { control.tabClosed(index) }
        function onTabAddClicked() { control.tabAddClicked() }
        function onTabDoubleClicked(index) { control.tabDoubleClicked(index) }
        function onTabsReordered(from, to) { control.tabsReordered(from, to) }
    }
}
