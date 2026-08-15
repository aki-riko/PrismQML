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
    // 拖到边缘时自动滚动 Flickable
    // FrameAnimation 跟随屏幕刷新率(120Hz/144Hz/240Hz 均逐帧驱动), 不绑 60fps
    FrameAnimation {
        id: _edgeAutoScrollTimer
        running: control._dragging
        onTriggered: {
            if (!control._dragging) return
            var edgeMargin = 40
            var visibleLeft = tabFlickable.contentX
            var visibleRight = visibleLeft + tabFlickable.width
            var pointerX = control._dragPointerRowX
            // step 按本帧实际时长(秒)换算为"每秒 480 像素"恒定速度
            // 对 60Hz: 8px/帧, 120Hz: 4px/帧, 240Hz: 2px/帧 — 视觉滚动速度一致
            var step = 480 * frameTime
            if (pointerX < visibleLeft + edgeMargin && tabFlickable.contentX > 0) {
                tabFlickable.contentX = Math.max(0, tabFlickable.contentX - step)
            } else if (pointerX > visibleRight - edgeMargin) {
                var maxX = Math.max(0, tabFlickable.contentWidth - tabFlickable.width)
                tabFlickable.contentX = Math.min(maxX, tabFlickable.contentX + step)
            }
        }
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

        Item {
            id: slidingIndicator
            // currentTab: itemAt() 非响应式 — 首帧 delegate 未建时返回 null, 之后也不会
            // 触发绑定重算, 导致 currentTab 永远卡 null → indicator 取兜底宽 60。
            // 用 _currentTabKey 做显式刷新信号: count/currentIndex/item 增删时 bump,
            // 强制 currentTab 绑定重新求值, 拿到真实 delegate item。
            property int _currentTabKey: 0
            property Item currentTab: {
                var _ = _currentTabKey  // 依赖刷新信号
                return (tabRepeater.count > 0 && control.currentIndex >= 0 && control.currentIndex < tabRepeater.count)
                       ? tabRepeater.itemAt(control.currentIndex) : null
            }
            // Preserve engine geometry while selection or model sync is pending.
            // 选择切换或模型同步待处理时保留引擎几何。
            property real tabLocalX: (_eng.running || !currentTab || _syncedIndex !== control.currentIndex || _syncedTab !== currentTab)
                                     ? _eng.indicatorX : currentTab.x
            property real targetWidth: (_eng.running || !currentTab || _syncedIndex !== control.currentIndex || _syncedTab !== currentTab)
                                       ? _eng.indicatorWidth : currentTab.width
            // 拖动期间叠加视觉位移,让 indicator 跟随被拖动/让位的 tab
            // 注意: 不能用 currentTab.visualOffsetX (var binding 不响应 _dragVisualIndex 变化),
            // 必须用 control 级状态自己推导
            property real tabVisualOffsetX: {
                if (!control._dragging) return 0
                var src = control._dragSourceIndex
                var vis = control._dragVisualIndex
                var cur = control.currentIndex
                if (cur === src) return control._dragSourceOffsetX
                // 当前选中不是源,但可能因 src 移动而需要让位
                var w = currentTab ? currentTab.width : 0
                if (src < vis) {
                    // 源向右拖, (src, vis] 区间向左让 1 位
                    if (cur > src && cur <= vis) return -w
                } else if (src > vis) {
                    // 源向左拖, [vis, src) 区间向右让 1 位
                    if (cur >= vis && cur < src) return w
                }
                return 0
            }
            property real scrollOffset: tabFlickable.contentX
            property real targetX: tabFlickable.x + tabLocalX + tabVisualOffsetX - scrollOffset + Enums.border.thin
            property real targetY: tabFlickable.y - tabBarBg.y + Enums.border.thin
            property real targetHeight: currentTab ? currentTab.height - Enums.spacing.xxs : Enums.controlSize.inputHeightLarge - Enums.spacing.s
            property bool _engInit: false
            property int _syncedIndex: -1
            property Item _syncedTab: null
            property real _layoutX: currentTab ? currentTab.x : 0
            property real _layoutW: currentTab ? currentTab.width : Enums.controlSize.segmentedMinWidth
            function _curRect() {
                var t = currentTab
                return t ? Qt.rect(t.x, 0, t.width, 1) : null
            }
            function _engineRect() {
                return Qt.rect(_eng.indicatorX, 0, _eng.indicatorWidth, 1)
            }
            function _scheduleSync(animate) {
                // Freeze the current interpolated frame before the zero-delay layout sync.
                // 在零延迟布局同步前冻结当前插值帧，避免旧目标再提交一帧。
                if (animate && _eng.running && _syncedIndex !== control.currentIndex) {
                    _eng.stopAnimation()
                }
                _syncTimer.animate = _syncTimer.animate || animate
                _syncTimer.restart()
            }
            function _runScheduledSync() {
                var animate = _syncTimer.animate
                _syncTimer.animate = false
                if (!currentTab || !_engInit) { syncIndicator(false); return }
                if (animate && _syncedIndex !== control.currentIndex) { syncIndicator(true); return }
                if (_syncedIndex === control.currentIndex) _followLayout()
            }
            function syncIndicator(animate) {
                var endRect = _curRect()
                if (!endRect) {
                    _eng.stopAnimation()
                    _engInit = false
                    _syncedIndex = -1
                    _syncedTab = null
                    return
                }
                if (animate && _engInit && _syncedIndex !== control.currentIndex) {
                    _eng.animateTo(_engineRect(), endRect)
                } else if (!_eng.running) {
                    _eng.setGeometry(endRect)
                }
                _engInit = true
                _syncedIndex = control.currentIndex
                _syncedTab = currentTab
            }
            function _followLayout() {
                if (!currentTab || !_engInit || _syncedIndex !== control.currentIndex) return
                // Flush the Row after delegate replacement before reading geometry.
                // 委托替换后先刷新 Row，再读取最终几何，避免瞬态 x=0 触发反向重定向。
                tabRow.forceLayout()
                var rect = _curRect()
                if (!rect) return
                _syncedTab = currentTab
                if (_eng.running) _eng.animateTo(_engineRect(), rect)
                else _eng.setGeometry(rect)
            }
            // The dragged source already renders the selected background itself.
            // 拖动源自身已渲染选中背景，拖动期间隐藏原指示器以避免鬼影。
            visible: tabRepeater.count > 0 && currentTab && _engInit && !control._dragging
            // Direct binding, follows scroll in real-time 直接绑定，滚动时实时跟随
            x: targetX
            y: targetY
            width: targetWidth
            height: targetHeight
            onCurrentTabChanged: _scheduleSync(false)
            Component.onCompleted: _scheduleSync(false)
            on_LayoutXChanged: _scheduleSync(false)
            on_LayoutWChanged: _scheduleSync(false)
            // Horizontal stretch engine driving tabLocalX and targetWidth 水平橡皮筋引擎
            // Selection animates; initialization snaps; layout changes retarget from the current frame. 选中切换使用橡皮筋；初始化瞬置；布局变化从当前帧重定向。
            SlidingIndicatorAnimation {
                id: _eng
                orientation: Qt.Horizontal
            }
            Timer {
                id: _syncTimer
                property bool animate: false
                interval: 0
                onTriggered: slidingIndicator._runScheduledSync()
            }
            // Selected tab indicator shadow 选中标签指示器投影
            // Fluent: 模糊阴影; neo: 硬阴影(NeoShadow)
            RectangularShadow {
                anchors.fill: indicatorBg
                radius: indicatorBg.radius
                color: Enums.shadow.level2.color
                blur: Enums.shadow.level2.blur
                offset.x: 0
                offset.y: Enums.shadow.level2.offset
                visible: control.shadowEnabled && Enums.usesSoftElevation
                         && !Enums.isNeumorphism
            }
            NeumorphicShadow {
                target: indicatorBg
                inset: true
                visible: control.shadowEnabled && Enums.isNeumorphism
                z: indicatorBg.z - 1
            }
            NeoShadow {
                target: indicatorBg
                visible: control.shadowEnabled && Enums.isNeobrutalism
                z: indicatorBg.z - 1
            }
            // Fluent Design selected tab background with border
            Rectangle {
                id: indicatorBg
                anchors.fill: parent
                radius: control._selectedTabRadius
                color: Enums.hasOutlinedSurfaces || Enums.isNeumorphism ? Enums.cardColor
                       : (Enums.isDark ? Enums.themeColors.tabSelectedDark : Enums.themeColors.tabSelectedLight)
                border.width: control._selectedTabBorderWidth
                border.color: Enums.hasOutlinedSurfaces ? Enums.borderColor
                       : (Enums.isDark ? Enums.stateColor.borderLight : Enums.stateColor.border)
            }
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
