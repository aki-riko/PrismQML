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
    property var tabs: []  // [{title, icon, content?}] or simple strings 结构化对象数组或简单字符串
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
    // Main axis of the strip; Qt.Horizontal behaves exactly as before
    // 条带主轴; Qt.Horizontal 与之前完全一致
    property int orientation: Qt.Horizontal
    // Vertical strip width; the horizontal counterpart is tabBarHeight
    // 纵向条带宽度; 横向的对应公开属性是 tabBarHeight
    property int stripWidth: Enums.controlSize.tabBarVerticalWidth

    readonly property var _safeTabs:
        tabs === null || tabs === undefined ? []
        : (typeof tabs.length === "number" ? tabs : [])

    // ==================== Internal Props 内部属性 ====================
    readonly property bool vertical: orientation === Qt.Vertical
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
    readonly property real _availableHeight: control.height - Enums.spacing.xs * 2 - (control.showAddButton ? Enums.controlSize.segmentedHeight : 0)
    // Vertical cells fill the strip instead of sizing to their content
    // 纵向单元填满标签条, 而不是按内容定宽
    readonly property real _verticalCellWidth: stripWidth - Enums.spacing.xs * 2
    // Only the strip matching the orientation owns delegates: the idle strip keeps
    // an empty model, so no duplicate delegate tree is ever built.
    // 只有与方向匹配的条带持有委托: 闲置条带模型为空, 不会构建重复委托树。
    readonly property Item tabRow: control.vertical ? verticalTabRow : horizontalTabRow
    readonly property var tabRepeater:
        control.vertical ? verticalTabRepeater : horizontalTabRepeater
    property int _dragSourceIndex: -1
    property int _dragVisualIndex: -1
    property real _dragSourceOffsetX: 0
    property real _dragPointerRowX: 0
    readonly property bool _dragging: _dragSourceIndex >= 0
    // Touch has no hover preview: on touch the hover treatment follows the press
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
    readonly property bool _touchActive: Touch.feedback(addHoverHandler.hovered, addTapHandler.pressed)

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
    contentWidth: control.vertical ? stripWidth : Enums.controlSize.chartDefaultWidth
    // A vertical strip is only as tall as its stacked rows; a horizontal one keeps
    // the historical bar height. 纵向条带高度取行堆叠高度; 横向保持历史条高。
    contentHeight: control.vertical
        ? Math.max(tabRow.height, control._tabHeight)
        : _tabBarHeight

    onCurrentIndexChanged: {
        currentChanged(currentIndex)
        if (tabFlickable) tabFlickable.scrollToCurrentTab()
        if (slidingIndicator) slidingIndicator._scheduleSync(true)
    }
    onOrientationChanged: {
        if (tabFlickable) tabFlickable.scrollToCurrentTab()
        if (slidingIndicator) slidingIndicator._scheduleSync(false)
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
        anchors.right: control.vertical ? undefined : parent.right
        anchors.bottom: control.vertical ? parent.bottom : undefined
        width: control.vertical ? control.stripWidth : undefined
        height: control.vertical ? undefined : control._tabBarHeight
        color: Enums.stateColor.cardDefaultBg
        clip: true

        TabIndicator {
            id: slidingIndicator
            host: control
            tabBar: tabBarBg
            tabFlickable: tabFlickable
            // Qualified on purpose: the strip is orientation-selected, and bare
            // names would resolve to TabIndicator's own required properties.
            // 必须显式限定: 条带按方向选择, 裸名会解析到 TabIndicator 自身的
            // required 属性上。
            tabRepeater: control.tabRepeater
            tabRow: control.tabRow
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
            if (control.vertical) {
                var itemTop = item.y
                var itemBottom = item.y + item.height
                if (itemTop < tabScrollHelper.targetPos)
                    smoothScrollTo(itemTop)
                else if (itemBottom > tabScrollHelper.targetPos + height)
                    smoothScrollTo(itemBottom - height)
                return
            }
            var itemLeft = item.x
            var itemRight = item.x + item.width
            if (itemLeft < tabScrollHelper.targetPos)
                smoothScrollTo(itemLeft)
            else if (itemRight > tabScrollHelper.targetPos + width)
                smoothScrollTo(itemRight - width)
        }

        // Horizontal: a top strip above the pages. Vertical: a left-hand column.
        // The cross axis carries the full cell thickness: strip height when
        // horizontal, cell width when vertical.
        // 横向: 位于页面上方的顶部条; 纵向: 位于页面左侧的竖列。
        // 副轴承载完整单元厚度: 横向为条带高度, 纵向为单元宽度。
        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.xs
        anchors.top: control.vertical ? parent.top : undefined
        anchors.topMargin: control.vertical ? Enums.spacing.xs : 0
        anchors.bottom: control.vertical ? undefined : tabBarBg.bottom
        anchors.bottomMargin: control.vertical
            ? 0 : (tabBarBg.height - control._tabHeight) / 2
        width: control.vertical
            ? control._verticalCellWidth
            : Math.min(tabRow.width, control._availableWidth)
        height: control.vertical
            ? Math.min(tabRow.height, control._availableHeight)
            : control._tabHeight
        contentWidth: control.vertical ? control._verticalCellWidth : tabRow.width
        contentHeight: control.vertical
            ? Math.max(tabRow.height, height) : control._tabHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        z: Enums.zIndex.header

        SmoothScrollHelper {
            id: tabScrollHelper
            target: tabFlickable
            orientation: control.vertical ? Qt.Vertical : Qt.Horizontal
            enabled: true
            bounceEnabled: true
            // Keep the historical TabWidget behavior: wheel input remains active
            // even when callers leave the compatibility property at its default.
            // 保持旧 TabWidget 行为：即使调用方使用默认值，滚轮仍可用。
            handleWheel: true
        }

        Row {
            id: horizontalTabRow
            objectName: "tabBarRow"
            visible: !control.vertical
            height: control._tabHeight
            spacing: Enums.spacing.none

            Repeater {
                id: horizontalTabRepeater
                model: control.vertical ? [] : control._safeTabs

                onItemAdded: slidingIndicator._currentTabKey++
                onItemRemoved: slidingIndicator._currentTabKey++

                TabItem {
                    host: control
                    rowContainer: horizontalTabRow
                    repeater: horizontalTabRepeater
                }
            }
        }

        Column {
            id: verticalTabRow
            objectName: "tabBarColumn"
            visible: control.vertical
            width: control._verticalCellWidth
            spacing: Enums.spacing.none

            Repeater {
                id: verticalTabRepeater
                model: control.vertical ? control._safeTabs : []

                onItemAdded: slidingIndicator._currentTabKey++
                onItemRemoved: slidingIndicator._currentTabKey++

                TabItem {
                    host: control
                    rowContainer: verticalTabRow
                    repeater: verticalTabRepeater
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
        anchors.left: control.vertical ? undefined : tabFlickable.right
        anchors.leftMargin: control.vertical ? 0 : Enums.spacing.xs
        anchors.horizontalCenter: control.vertical ? tabBarBg.horizontalCenter : undefined
        anchors.top: control.vertical ? tabFlickable.bottom : undefined
        anchors.topMargin: control.vertical ? Enums.spacing.xs : 0
        anchors.bottom: control.vertical ? undefined : tabBarBg.bottom
        anchors.bottomMargin: control.vertical
            ? 0 : (control._tabBarHeight - Enums.controlSize.closeButtonSize) / 2
        z: Enums.zIndex.controls
        color: control._touchActive ? Enums.stateColor.hover : Enums.transparent

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
            id: addTapHandler
            enabled: control.interactionEnabled
            onTapped: control.tabAddClicked()
        }
    }
}
