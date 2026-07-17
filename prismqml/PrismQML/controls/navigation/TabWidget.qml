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

    // ==================== Internal Props 内部属性 ====================
    readonly property int _tabHeight: Enums.controlSize.inputHeightLarge - Enums.spacing.xs
    readonly property int _tabBarHeight: Enums.controlSize.tableHeaderHeight
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
        var newTabs = tabs.slice()
        newTabs.push({title: title, icon: icon || "", content: content})
        tabs = newTabs
        return tabs.length - 1
    }
    
    // Insert a tab at index 在指定位置插入标签
    function insertTab(index, title, icon, content) {
        var newTabs = tabs.slice()
        var idx = Math.max(0, Math.min(index, newTabs.length))
        newTabs.splice(idx, 0, {title: title, icon: icon || "", content: content})
        tabs = newTabs
        return idx
    }
    
    // Remove tab at index 移除指定位置的标签
    function removeTab(index) {
        if (index < 0 || index >= tabs.length) return
        var newTabs = tabs.slice()
        newTabs.splice(index, 1)
        tabs = newTabs
        if (currentIndex >= tabs.length) {
            currentIndex = Math.max(0, tabs.length - 1)
        }
    }
    
    // Clear all tabs 清空所有标签
    function clear() {
        tabs = []
        currentIndex = 0
    }
    
    // Get tab count 获取标签数量
    function count() {
        return tabs.length
    }
    
    // Get tab text 获取标签文本
    function tabText(index) {
        if (index < 0 || index >= tabs.length) return ""
        return tabs[index].title || ""
    }
    
    // Set tab text 设置标签文本
    function setTabText(index, text) {
        if (index < 0 || index >= tabs.length) return
        var newTabs = tabs.slice()
        newTabs[index] = Object.assign({}, newTabs[index], {title: text})
        tabs = newTabs
    }
    
    // Get tab icon 获取标签图标
    function tabIcon(index) {
        if (index < 0 || index >= tabs.length) return ""
        return tabs[index].icon || ""
    }
    
    // Set tab icon 设置标签图标
    function setTabIcon(index, icon) {
        if (index < 0 || index >= tabs.length) return
        var newTabs = tabs.slice()
        newTabs[index] = Object.assign({}, newTabs[index], {icon: icon})
        tabs = newTabs
    }
    
    // Set current index 设置当前索引
    function setCurrentIndex(index) {
        if (index >= 0 && index < tabs.length) {
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
            Connections {
                function onCurrentIndexChanged() { slidingIndicator._scheduleSync(true) }
                target: control
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
                visible: control.shadowEnabled && !Enums.isNeobrutalism
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
                radius: Enums.isNeobrutalism ? Enums.neo.radius : (Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.card)
                color: Enums.isNeobrutalism ? Enums.neo.surface
                       : (Enums.isPrismDesign ? Enums.stateColor.segmentedSelected : (Enums.isDark ? Enums.themeColors.tabSelectedDark : Enums.themeColors.tabSelectedLight))
                border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
                border.color: Enums.isNeobrutalism ? Enums.neo.borderColor
                       : (Enums.isPrismDesign ? Enums.stateColor.segmentedSelectedBorder : (Enums.isDark ? Enums.stateColor.borderLight : Enums.stateColor.border))
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
                model: control.tabs

                // delegate 创建/销毁时刷新 currentTab (itemAt 非响应式, 必须显式触发)
                onItemAdded: slidingIndicator._currentTabKey++
                onItemRemoved: slidingIndicator._currentTabKey++

                Item {
                    id: tabItem
                    // Width adapts to content 宽度根据内容自适应
                    // Left and right padding spacing.xl (16) each 左右内边距各 spacing.xl (16)
                    width: Math.max(Enums.controlSize.segmentedMinWidth,
                                    tabContent.implicitWidth + Enums.spacing.xl * 2 + (control.closable ? Enums.spacing.xxl : 0))
                    height: control._tabHeight

                    property bool selected: index === control.currentIndex
                    property bool hovered: tabHoverHandler.hovered
                    property bool pressed: tabTapHandler.pressed

                    // 拖拽相关 ============================================================
                    readonly property bool isDragSource: control._dragging && index === control._dragSourceIndex
                    readonly property int visualIndex: {
                        if (!control._dragging) return index
                        var src = control._dragSourceIndex
                        var vis = control._dragVisualIndex
                        if (index === src) return vis
                        if (src < vis) {
                            if (index > src && index <= vis) return index - 1
                        } else if (src > vis) {
                            if (index >= vis && index < src) return index + 1
                        }
                        return index
                    }
                    readonly property real visualOffsetX: {
                        if (!control._dragging) return 0
                        if (isDragSource) return control._dragSourceOffsetX
                        return (visualIndex - index) * width
                    }

                    transform: Translate {
                        x: tabItem.visualOffsetX
                        Behavior on x {
                            enabled: !tabItem.isDragSource
                            NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic }
                        }
                    }
                    z: isDragSource ? Enums.zIndex.controlsAbove : Enums.zIndex.base
                    // 实色显示,避免半透明造成"鬼影"观感
                    opacity: 1.0
                    // ====================================================================

                    // Background (non-selected state) 背景（非选中状态）
                    // Fluent Design: hover/pressed 有微妙的背景变化
                    Rectangle {
                        id: tabBg
                        anchors.fill: parent
                        anchors.margins: Enums.border.thin
                        anchors.bottomMargin: Enums.border.thin
                        radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.card
                        color: {
                            // 拖拽中的源 tab (含选中态 source): 用稍深 hover 背景 + 边框,
                            // 视觉上像"被抓起来",但不与 selected 同色避免割裂感
                            if (tabItem.isDragSource) {
                                return Enums.stateColor.tabDragSource
                            }
                            if (tabItem.selected) return Enums.transparent
                            // Fluent Design pressed state Fluent Design 按下状态
                            if (tabItem.pressed) {
                                return Enums.stateColor.tabPressed
                            }
                            // Fluent Design hover state Fluent Design 悬浮状态
                            if (tabItem.hovered) {
                                return Enums.stateColor.hover
                            }
                            return Enums.transparent
                        }
                        // 拖拽中的源 tab 加细边框,提示"被抓起来"的视觉
                        border.width: tabItem.isDragSource ? Enums.border.thin : 0
                        border.color: Enums.isPrismDesign ? Enums.stateColor.borderLight : (Enums.isDark ? Enums.stateColor.borderLight : Enums.stateColor.border)

                        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                    }

                    // Content - Fluent Design style 内容 - Fluent Design风格
                    Row {
                        id: tabContent
                        anchors.centerIn: parent
                        anchors.horizontalCenterOffset: control.closable ? -Enums.spacing.l : 0
                        spacing: Enums.spacing.s

                        // Icon 图标
                        Label {
                            id: tabIcon
                            type: Enums.label.type_body
                            text: modelData && modelData.icon ? modelData.icon : ""
                            visible: text !== ""
                            anchors.verticalCenter: parent.verticalCenter
                            opacity: tabItem.selected ? Enums.opacityLevel.visible : (Enums.isDark ? Enums.opacityLevel.strong : Enums.opacityLevel.secondary)
                            color: Enums.foregroundColor

                            Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
                        }

                        // Text 文字
                        Label {
                            id: tabText
                            type: Enums.label.type_caption
                            text: modelData.title || modelData
                            color: Enums.foregroundColor
                            anchors.verticalCenter: parent.verticalCenter
                            opacity: tabItem.selected ? Enums.opacityLevel.visible : (Enums.isDark ? Enums.opacityLevel.strong : Enums.opacityLevel.secondary)

                            Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
                        }
                    }

                    // Close button 关闭按钮
                    CloseButton {
                        id: closeBtn
                        anchors.right: parent.right
                        anchors.rightMargin: Enums.spacing.s
                        anchors.verticalCenter: parent.verticalCenter
                        size: Enums.iconSize.xxl
                        iconSizeValue: Enums.iconSize.tiny
                        normalIconColor: Enums.secondaryForeground
                        visible: control.closable && (tabItem.selected || tabItem.hovered)
                        z: Enums.zIndex.header  // Above indicator 在指示器之上
                        onClicked: control.tabClosed(index)
                    }

                    // HoverHandler for stable hover 使用HoverHandler实现稳定hover
                    HoverHandler {
                        id: tabHoverHandler
                        cursorShape: Qt.PointingHandCursor
                    }

                    // TapHandler for click 使用TapHandler处理点击
                    TapHandler {
                        id: tabTapHandler
                        onTapped: {
                            control.currentIndex = index
                            control.tabClicked(index)
                        }
                    }

                    // ==================== DragHandler 拖拽重排 ====================
                    DragHandler {
                        id: tabDragHandler
                        enabled: control.movable
                        target: null
                        xAxis.enabled: true
                        yAxis.enabled: false
                        dragThreshold: 6

                        // gesture 开始时记录指针在 tabRow 内的 x (不受 tabItem transform 影响)
                        property real _pressRowX: 0

                        onActiveChanged: {
                            if (active) {
                                control._dragSourceIndex = index
                                control._dragVisualIndex = index
                                // pressPosition 是相对 tabItem 的局部坐标,但 tabItem 此刻 transform=0,等价
                                var pt = tabItem.mapToItem(tabRow, centroid.pressPosition.x, centroid.pressPosition.y)
                                _pressRowX = pt.x
                                control._dragPointerRowX = pt.x
                                control._dragSourceOffsetX = 0
                            } else if (control._dragSourceIndex >= 0) {
                                var owner = control
                                var from = control._dragSourceIndex
                                var to = control._dragVisualIndex
                                control._dragSourceIndex = -1
                                control._dragVisualIndex = -1
                                control._dragSourceOffsetX = 0
                                if (from !== to && from >= 0 && to >= 0) {
                                    owner.tabsReordered(from, to)
                                    owner.currentIndex = to
                                }
                            }
                        }

                        // activeTranslation.x: gesture 开始至今的 x 位移,绝对值,不受 transform 干扰
                        onActiveTranslationChanged: {
                            if (!active) return
                            control._dragSourceOffsetX = activeTranslation.x
                            // 当前指针在 tabRow 的 x = 起始 row x + 累计位移 (用于边缘滚动)
                            var pointerRowX = _pressRowX + activeTranslation.x
                            control._dragPointerRowX = pointerRowX
                            // visualIndex 切换基于"源 tab 中心位置",不是指针,避免按下点偏离中心导致让位太早造成视觉重叠
                            var w = tabItem.width
                            if (w <= 0) return
                            var sourceCenterRowX = index * w + activeTranslation.x + w / 2
                            var newVisual = Math.max(0, Math.min(control.tabs.length - 1,
                                                                  Math.floor(sourceCenterRowX / w)))
                            if (newVisual !== control._dragVisualIndex) {
                                control._dragVisualIndex = newVisual
                            }
                        }
                    }
                    // ==============================================================

                    // Right separator 右侧分隔线
                    Separator {
                        id: separator
                        type: Enums.separator.vertical
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        lineLength: Enums.iconSize.small
                        visible: {
                            if (control._dragging) return false  // 拖动期间隐藏分隔线避免视觉干扰
                            // Don't show for last tab 最后一个标签不显示
                            if (index >= control.tabs.length - 1) return false
                            // Don't show when current or next tab is selected 当前标签或下一个标签选中时不显示
                            if (tabItem.selected) return false
                            if (index + 1 === control.currentIndex) return false
                            // Don't show when current or next tab is hovered 当前标签或下一个标签hover时不显示
                            if (tabItem.hovered) return false
                            var nextItem = tabRepeater.itemAt(index + 1)
                            if (nextItem && nextItem.hovered) return false
                            return true
                        }
                    }
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
    Rectangle {
        id: contentArea
        anchors.top: tabBarBg.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        color: Enums.cardColor
        clip: true  // 裁掉滑入/滑出时露在区域外的内容

        Repeater {
            model: control.tabs

            Loader {
                id: pageLoader
                width: contentArea.width
                height: contentArea.height
                y: 0
                sourceComponent: (modelData.content && typeof modelData.content === 'object') ? modelData.content : null

                readonly property bool isCurrent: index === control.currentIndex
                // 动画期间(自身正在滑出)保持 active+visible, 否则卸载省资源
                property bool _animatingOut: false
                active: isCurrent || _animatingOut
                visible: active

                // 胶片模型: 所有页并排, 第 i 页停在 (i - currentIndex)*width。
                // 当前页 x=0; 切到更大 index → 整条胶片左移(旧页滑出左侧, 新页从右侧进);
                // 切到更小 index → 右移。方向天然自适应, 无需单独记方向。
                x: (index - control.currentIndex) * contentArea.width

                Behavior on x {
                    enabled: !control._dragging
                    NumberAnimation {
                        duration: Enums.duration.slow
                        easing.type: Easing.OutCubic
                        // 旧页滑出动画结束 → 卸载
                        onRunningChanged: if (!running && !pageLoader.isCurrent) pageLoader._animatingOut = false
                    }
                }

                // 成为旧页(刚被切走)时, 标记为正在滑出, 维持 active 直到动画结束
                onIsCurrentChanged: if (!isCurrent) _animatingOut = true
            }
        }
    }
}
