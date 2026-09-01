// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/navigation/_internal"
import "_internal"
import "_internal/NavigationLayout.js" as NavigationLayout

// ToggleNavigationBar - Navigation bar with toggle buttons 切换按钮导航栏
// Mutually exclusive selection with sliding indicator 互斥选中带滑动指示器
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var model: []
    property var bottomItems: []
    property int currentIndex: 0
    property color backgroundColor: Enums.transparent
    property bool fillWidth: true
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.navigationScroll
    property real scrollStep: Enums.spacing.navigationScrollStep
    // Fade items near an overflowing edge to hint the list scrolls 溢出端渐隐以提示可滚动
    property bool scrollFadeEnabled: true
    // Reveal a thin overlay rail on hover 悬停时显形细浮层滚动轨
    property bool scrollRailEnabled: true
    // Let touch and mouse drag scroll the list 允许触摸与鼠标拖拽滚动列表
    property bool dragScrollEnabled: true

    // ==================== Internal Props 内部属性 ====================
    readonly property var _safeModel:
        model === null || model === undefined ? []
        : (typeof model.length === "number" ? model : [])
    readonly property var _safeBottomItems:
        bottomItems === null || bottomItems === undefined ? []
        : (typeof bottomItems.length === "number" ? bottomItems : [])

    // Maps key to page index for bottom page items 将 key 映射到页面索引，用于底部页面项
    property var _bottomPageIndexMap: ({})
    property bool _skipIndicatorAnimation: false
    property int _refreshTrigger: 0
    // Hide the shared indicator when the selected page has no visible nav item.
    // 当前页面没有可见导航项时隐藏共享选中指示器。
    property bool _indicatorVisible: true
    
    // Track if indicator is controlled by bottom page item
    property bool _bottomItemActive: false
    
    // Scroll offset for real-time indicator tracking 指示器实时跟踪的滚动偏移
    property real _scrollOffset: topFlickable.contentY

    // ==================== Readonly State 只读状态 ====================
    // 选中项的渐隐值; 底部固定项不在滚动区内, 不参与渐隐。
    readonly property real _selectedItemFade: scrollFade.selectionOpacity(
        control._getItemAt(control.currentIndex),
        !control._bottomItemActive
            && control.currentIndex >= 0
            && control.currentIndex < control._safeModel.length)

    // ==================== Signals 信号 ====================
    signal itemClicked(int index)
    signal bottomItemClicked(int index)

    // ==================== Public Methods 公开方法 ====================
    function smoothScrollTo(targetY) { topScrollBehavior.scrollTo(targetY) }
    function smoothScrollBy(delta) { topScrollBehavior.scrollBy(delta) }

    // ==================== Internal Methods 内部方法 ====================
    function _getItemAt(globalIndex) {
        if (globalIndex < 0) return null
        if (globalIndex < _safeModel.length) {
            return topRep.itemAt(globalIndex)
        }
        var bottomIndex = globalIndex - _safeModel.length
        if (bottomIndex < _safeBottomItems.length) {
            return bottomRep.itemAt(bottomIndex)
        }
        return null
    }
    
    // 构造指示器矩形 (整块胶囊, 横向占满, 纵向随 item)
    function _rectFor(y, h) {
        return Qt.rect(Enums.spacing.xs, y,
                       control.width - Enums.spacing.xs * 2, h)
    }

    function _applyIndicator(y, h, animate) {
        var endRect = _rectFor(y, h)
        if (animate && slidingIndicator._initialized) {
            slidingIndicator.startAnimation(slidingIndicator.getIndicatorRect(), endRect)
        } else {
            slidingIndicator.setGeometry(endRect)
        }
    }

    function _updateIndicator(animate) {
        var item = _getItemAt(currentIndex)
        control._indicatorVisible = !!item && (!item.modelData || item.modelData.visible !== false)
        if (!control._indicatorVisible) {
            slidingIndicator.stopAnimation()
            return
        }
        // Skip if bottom item is active (indicator controlled by updateIndicatorForBottomItem) 如果底部项激活则跳过（指示器由 updateIndicatorForBottomItem 控制）
        if (_bottomItemActive) return
        // Map item position to control coordinate 映射到control坐标系
        var mappedPos = item.mapToItem(control, 0, 0)
        _applyIndicator(mappedPos.y, item.height, animate)
    }

    // Update indicator for bottom page item by key 通过 key 更新底部页面项的指示器
    function updateIndicatorForBottomItem(key) {
        if (!key) return
        // Delay to ensure Repeater items are ready 延迟以确保 Repeater 项已准备好
        Qt.callLater(function() {
            for (var i = 0; i < _safeBottomItems.length; i++) {
                if (_safeBottomItems[i] && _safeBottomItems[i].key === key) {
                    var item = bottomRep.itemAt(i)
                    control._indicatorVisible = !!item && (!item.modelData || item.modelData.visible !== false)
                    if (!control._indicatorVisible) {
                        _bottomItemActive = false
                        slidingIndicator.stopAnimation()
                        return
                    }
                    if (item) {
                        var mappedPos = item.mapToItem(control, 0, 0)
                        _bottomItemActive = true  // Mark bottom item as active 标记底部项激活
                        _applyIndicator(mappedPos.y, item.height, true)
                    }
                    break
                }
            }
        })
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: fillWidth ? (parent ? parent.width : Enums.window.navPanelMinWidth) : (topLayout.width + Enums.spacing.m * 2)
    implicitHeight: parent ? parent.height : Enums.window.defaultHeight

    onCurrentIndexChanged: Qt.callLater(function() { if (!_skipIndicatorAnimation) _updateIndicator(true) })
    Component.onCompleted: Qt.callLater(function() { _updateIndicator(false) })

    // Real-time indicator tracking when scrolling 滚动时实时跟踪指示器
    on_ScrollOffsetChanged: {
        _indicatorTracker._scrolling = true
        _scrollStopTimer.restart()
        _updateIndicator(false)
    }

    ToggleNavigationIndicatorTrackerTimer {
        id: _indicatorTracker
        host: control
    }
    
    NavigationIndicatorScrollStopTimer {
        id: _scrollStopTimer
        tracker: _indicatorTracker
    }
    
    // ==================== Content 内容 ====================
    // Background 背景
    Rectangle {
        anchors.fill: parent
        color: control.backgroundColor
    }
    
    // Sliding indicator (shared vertical sticky base) 滑动指示器（统一垂直粘滞基类）
    SlidingIndicator {
        id: slidingIndicator
        orientation: Qt.Vertical
        z: Enums.zIndex.content  // Below bottom cover 低于底部遮盖层
        radius: Enums.radius.small
        visible: (control._safeModel.length + control._safeBottomItems.length) > 0
            && control._indicatorVisible
        // Keep the capsule in lockstep with the item it marks 胶囊与所标记的项锁步渐隐
        opacity: control._selectedItemFade
    }

    // Edge fade state shared by the items and the indicator 导航项与指示器共用的渐隐状态
    NavigationScrollFade {
        id: scrollFade
        objectName: "toggleNavigationBarScrollFade"
        flickable: topFlickable
        active: control.scrollFadeEnabled
        itemHeight: Enums.controlSize.buttonHeight + Enums.spacing.xs
        itemCount: topRep.count
    }

    // 被动悬停探测, 不抢委托的 TapHandler 事件 Passive hover, steals no delegate events
    HoverHandler { id: hostHover }
    
    // Top navigation items 顶部导航项
    Flickable {
        id: topFlickable
        z: 1  // Content layer 内容层
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: Enums.spacing.xs
        anchors.leftMargin: Enums.spacing.xs
        anchors.rightMargin: Enums.spacing.xs
        height: Math.max(0, parent.height - bottomLayout.height - Enums.spacing.xs * 2)
        
        contentWidth: width
        contentHeight: topLayout.height
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        // 委托用 TapHandler, 与 Flickable 手势天然协作。
        // The delegates use TapHandler, which cooperates with Flickable natively.
        interactive: control.dragScrollEnabled
        
        Item {
            id: topLayout
            width: parent.width
            height: NavigationLayout.contentHeight(
                control._safeModel,
                Enums.controlSize.buttonHeight,
                Enums.spacing.xs)
            
            Repeater {
                id: topRep
                model: control._safeModel
                
                onItemAdded: Qt.callLater(function() { control._updateIndicator(false) })
                
                delegate: ToggleNavigationBarItem {
                    id: topNavItem

                    required property int index
                    required property var modelData

                    // 供 objectName 定位与外部读取 For lookup and external reads
                    readonly property string itemText: text
                    readonly property bool itemVisible: !modelData || modelData.visible !== false

                    visible: itemVisible
                    text: modelData ? (modelData.text || "") : ""
                    icon: modelData ? (modelData.icon || "") : ""
                    selected: itemVisible && index === control.currentIndex

                    width: itemVisible
                        ? (control.fillWidth ? topLayout.width : contentWidth)
                        : 0
                    height: itemVisible ? Enums.controlSize.buttonHeight : 0
                    y: NavigationLayout.itemY(
                        control._safeModel,
                        index,
                        Enums.controlSize.buttonHeight,
                        Enums.spacing.xs)
                    opacity: scrollFade.opacityAt(y, height)

                    onClicked: {
                        control._bottomItemActive = false  // Clear bottom item state 清除底部项状态
                        control.currentIndex = topNavItem.index
                        control.itemClicked(topNavItem.index)
                    }
                }
            }
        }

        NavigationSmoothScroll {
            id: topScrollBehavior
            helperName: "toggleNavigationBarSmoothScrollHelper"
            flickable: topFlickable
            smoothScroll: control.smoothScroll
            duration: control.scrollDuration
            step: control.scrollStep
        }
    }

    // 浮层滚动轨: 与 topFlickable 同级, 不在其内部 —— 放进去会随内容一起滚动。
    // Overlay rail as a sibling of topFlickable; inside, it would scroll away.
    NavigationScrollRail {
        objectName: "toggleNavigationBarScrollRail"
        flickable: topFlickable
        active: control.scrollRailEnabled
        hostHovered: hostHover.hovered
    }
    
    // Bottom fixed items 底部固定项
    // Background to cover indicator when scrolling 滚动时遮盖指示器的背景
    Rectangle {
        id: bottomCover
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: bottomLayout.height + Enums.spacing.xs * 2
        color: control.backgroundColor.a > 0 ? control.backgroundColor : Enums.backgroundColor
        z: Enums.zIndex.controls  // Above indicator 高于指示器
    }
    
    Item {
        id: bottomLayout
        height: NavigationLayout.contentHeight(
            control._safeBottomItems,
            Enums.controlSize.buttonHeight,
            Enums.spacing.xs)
        z: Enums.zIndex.controls + 1  // Above cover and indicator 高于遮盖层和指示器
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottomMargin: Enums.spacing.xs
        anchors.leftMargin: Enums.spacing.xs
        anchors.rightMargin: Enums.spacing.xs
        
        Repeater {
            id: bottomRep
            model: control._safeBottomItems
            
            onItemAdded: Qt.callLater(control._updateIndicator)
            
            delegate: ToggleNavigationBarItem {
                id: bottomNavItem

                required property int index
                required property var modelData

                readonly property int globalIndex: control._safeModel.length + index
                // 供 objectName 定位与外部读取 For lookup and external reads
                readonly property string itemText: text
                readonly property bool itemSelectable: !modelData || modelData.selectable !== false
                readonly property bool itemVisible: !modelData || modelData.visible !== false

                visible: itemVisible
                text: modelData ? (modelData.text || "") : ""
                icon: modelData ? (modelData.icon || "") : ""
                width: itemVisible
                    ? (control.fillWidth ? bottomLayout.width : contentWidth)
                    : 0
                height: itemVisible ? Enums.controlSize.buttonHeight : 0
                y: NavigationLayout.itemY(
                    control._safeBottomItems,
                    index,
                    Enums.controlSize.buttonHeight,
                    Enums.spacing.xs)

                // Bottom page items use key to find page index 底部页面项通过 key 查找页面索引来判断渲染状态
                selected: {
                    if (!itemVisible) return false
                    var item = control._safeBottomItems[index]
                    var hasKey = item && item.key !== undefined
                    var isSelectable = item && item.selectable !== false
                    if (hasKey && isSelectable) {
                        // Page item: check if current page matches key 页面项：检查当前页面是否匹配 key
                        return control.currentIndex === control._bottomPageIndexMap[item.key]
                    }
                    return false  // Function items are never selected 功能项永不选中
                }

                // Always emit signal, let window handle page switch 始终发送信号，让窗口组件处理页面切换
                onClicked: control.bottomItemClicked(bottomNavItem.index)
            }
        }
    }
}
