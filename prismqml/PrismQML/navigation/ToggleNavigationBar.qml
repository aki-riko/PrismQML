// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/buttons/Button"
import "../controls/icons"
import "../controls/data/Label"
import "../controls/navigation/_internal"

// ToggleNavigationBar - Navigation bar with toggle buttons 切换按钮导航栏
// Mutually exclusive selection with sliding indicator 互斥选中带滑动指示器
Item {
    id: control
    
    // ==================== Props 属性 ====================
    property var model: []
    property var bottomItems: []
    property int currentIndex: 0
    property color backgroundColor: Enums.transparent
    property bool fillWidth: true
    
    // ==================== Bottom Page Index Map 底部页面索引映射 ====================
    // Maps key to page index for bottom page items 将 key 映射到页面索引，用于底部页面项
    property var _bottomPageIndexMap: ({})
    property bool _skipIndicatorAnimation: false
    
    // ==================== Signals 信号 ====================
    signal itemClicked(int index)
    signal bottomItemClicked(int index)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: fillWidth ? (parent ? parent.width : Enums.window.navPanelMinWidth) : (topLayout.width + Enums.spacing.m * 2)
    implicitHeight: parent ? parent.height : Enums.window.defaultHeight
    
    // ==================== Internal 内部属性 ====================
    property int _refreshTrigger: 0
    
    // Track if indicator is controlled by bottom page item
    property bool _bottomItemActive: false
    
    // Scroll offset for real-time indicator tracking 指示器实时跟踪的滚动偏移
    property real _scrollOffset: topFlickable.contentY
    
    // ==================== Helper Functions 辅助函数 ====================
    function _getItemAt(globalIndex) {
        if (globalIndex < 0) return null
        if (globalIndex < model.length) {
            return topRep.itemAt(globalIndex)
        }
        var bottomIndex = globalIndex - model.length
        if (bottomIndex < bottomItems.length) {
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
        // Skip if bottom item is active (indicator controlled by updateIndicatorForBottomItem) 如果底部项激活则跳过（指示器由 updateIndicatorForBottomItem 控制）
        if (_bottomItemActive) return

        var item = _getItemAt(currentIndex)
        if (!item) return
        // Map item position to control coordinate 映射到control坐标系
        var mappedPos = item.mapToItem(control, 0, 0)
        _applyIndicator(mappedPos.y, item.height, animate)
    }

    // Update indicator for bottom page item by key 通过 key 更新底部页面项的指示器
    function updateIndicatorForBottomItem(key) {
        if (!key) return
        // Delay to ensure Repeater items are ready 延迟以确保 Repeater 项已准备好
        Qt.callLater(function() {
            for (var i = 0; i < bottomItems.length; i++) {
                if (bottomItems[i].key === key) {
                    var item = bottomRep.itemAt(i)
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

    onCurrentIndexChanged: Qt.callLater(function() { if (!_skipIndicatorAnimation) _updateIndicator(true) })
    Component.onCompleted: Qt.callLater(function() { _updateIndicator(false) })

    // Real-time indicator tracking when scrolling 滚动时实时跟踪指示器
    on_ScrollOffsetChanged: {
        _indicatorTracker._scrolling = true
        _scrollStopTimer.restart()
        _updateIndicator(false)
    }

    Timer {
        id: _indicatorTracker
        interval: Enums.duration.tick
        repeat: true
        running: _scrolling
        property bool _scrolling: false
        onTriggered: control._updateIndicator(false)
    }
    
    Timer {
        id: _scrollStopTimer
        interval: Enums.duration.fast
        onTriggered: _indicatorTracker._scrolling = false
    }
    
    // ==================== Background 背景 ====================
    Rectangle {
        anchors.fill: parent
        color: control.backgroundColor
    }
    
    // ==================== Sliding Indicator 滑动指示器 (统一基类, 垂直橡皮筋粘滞) ====================
    SlidingIndicator {
        id: slidingIndicator
        orientation: Qt.Vertical
        z: Enums.zIndex.content  // Below bottom cover 低于底部遮盖层
        radius: Enums.radius.small
        visible: (control.model.length + control.bottomItems.length) > 0
    }
    
    // ==================== Top Nav Items 顶部导航项 ====================
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
        interactive: contentHeight > height
        
        Column {
            id: topLayout
            width: parent.width
            spacing: Enums.spacing.xs
            
            Repeater {
                id: topRep
                model: control.model
                
                onItemAdded: Qt.callLater(function() { control._updateIndicator(false) })
                
                delegate: Item {
                    id: topNavItem
                    width: control.fillWidth ? topLayout.width : topNavContent.implicitWidth
                    height: Enums.controlSize.buttonHeight
                    
                    required property int index
                    required property var modelData
                    
                    readonly property string itemText: modelData.text || ""
                    readonly property string itemIcon: modelData.icon || ""
                    readonly property bool selected: index === control.currentIndex
                    readonly property bool hovered: topHoverHandler.hovered
                    readonly property bool pressed: topTapHandler.pressed
                    
                    Rectangle {
                        anchors.fill: parent
                        radius: Enums.radius.small
                        visible: !topNavItem.selected && (topNavItem.hovered || topNavItem.pressed)
                        color: topNavItem.pressed ? Enums.stateColor.transparentPressed : 
                               topNavItem.hovered ? Enums.stateColor.transparentHover : 
                               Enums.transparent
                    }
                    
                    Row {
                        id: topNavContent
                        anchors.left: parent.left
                        anchors.leftMargin: Enums.spacing.m
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: topNavItem.itemIcon !== "" && topNavItem.itemText !== "" ? Enums.spacing.s : 0
                        
                        Icon {
                            icon: topNavItem.itemIcon
                            iconSize: Enums.iconSize.m
                            color: topNavItem.selected ? Enums.accentForeground : Enums.textColor.primary
                            visible: topNavItem.itemIcon !== ""
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        
                        Label {
                            type: Enums.label.type_body
                            text: topNavItem.itemText
                            color: topNavItem.selected ? Enums.accentForeground : Enums.textColor.primary
                            visible: topNavItem.itemText !== ""
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                    
                    HoverHandler { id: topHoverHandler; cursorShape: Qt.PointingHandCursor }
                    TapHandler { 
                        id: topTapHandler
                        onTapped: { 
                            control._bottomItemActive = false  // Clear bottom item state 清除底部项状态
                            control.currentIndex = topNavItem.index
                            control.itemClicked(topNavItem.index) 
                        } 
                    }
                }
            }
        }
    }
    
    // ==================== Bottom Fixed Items 底部固定项 ====================
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
    
    Column {
        id: bottomLayout
        z: Enums.zIndex.controls + 1  // Above cover and indicator 高于遮盖层和指示器
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottomMargin: Enums.spacing.xs
        anchors.leftMargin: Enums.spacing.xs
        anchors.rightMargin: Enums.spacing.xs
        spacing: Enums.spacing.xs
        
        Repeater {
            id: bottomRep
            model: control.bottomItems
            
            onItemAdded: Qt.callLater(control._updateIndicator)
            
            delegate: Item {
                id: bottomNavItem
                width: control.fillWidth ? bottomLayout.width : bottomNavContent.implicitWidth
                height: Enums.controlSize.buttonHeight
                
                required property int index
                required property var modelData
                
                readonly property int globalIndex: control.model.length + index
                readonly property string itemText: modelData.text || ""
                readonly property string itemIcon: modelData.icon || ""
                readonly property bool itemSelectable: modelData.selectable !== false
                // Bottom page items use key to find page index 底部页面项通过 key 查找页面索引来判断渲染状态
                readonly property bool selected: {
                    var item = control.bottomItems[index]
                    var hasKey = item && item.key !== undefined
                    var isSelectable = item && item.selectable !== false
                    if (hasKey && isSelectable) {
                        // Page item: check if current page matches key 页面项：检查当前页面是否匹配 key
                        return control.currentIndex === control._bottomPageIndexMap[item.key]
                    }
                    return false  // Function items are never selected 功能项永不选中
                }
                readonly property bool hovered: bottomHoverHandler.hovered
                readonly property bool pressed: bottomTapHandler.pressed
                
                // Opaque background to cover sliding indicator 不透明背景覆盖滑动指示器
                Rectangle {
                    anchors.fill: parent
                    color: control.backgroundColor.a > 0 ? control.backgroundColor : Enums.backgroundColor
                    visible: false
                }
                
                // Selected background 选中背景
                Rectangle {
                    anchors.fill: parent
                    radius: Enums.radius.small
                    color: Enums.accentColor
                    visible: false
                }
                
                // Hover/Pressed background 悬停/按下背景
                Rectangle {
                    anchors.fill: parent
                    radius: Enums.radius.small
                    visible: !bottomNavItem.selected && (bottomNavItem.hovered || bottomNavItem.pressed)
                    color: bottomNavItem.pressed ? Enums.stateColor.transparentPressed : 
                           bottomNavItem.hovered ? Enums.stateColor.transparentHover : 
                           Enums.transparent
                }
                
                Row {
                    id: bottomNavContent
                    anchors.left: parent.left
                    anchors.leftMargin: Enums.spacing.m
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: bottomNavItem.itemIcon !== "" && bottomNavItem.itemText !== "" ? Enums.spacing.s : 0
                    
                    Icon {
                        icon: bottomNavItem.itemIcon
                        iconSize: Enums.iconSize.m
                        color: bottomNavItem.selected ? Enums.accentForeground : Enums.textColor.primary
                        visible: bottomNavItem.itemIcon !== ""
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    Label {
                        type: Enums.label.type_body
                        text: bottomNavItem.itemText
                        color: bottomNavItem.selected ? Enums.accentForeground : Enums.textColor.primary
                        visible: bottomNavItem.itemText !== ""
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                
                HoverHandler { id: bottomHoverHandler; cursorShape: Qt.PointingHandCursor }
                TapHandler { 
                    id: bottomTapHandler
                    onTapped: {
                        // Always emit signal, let window handle page switch 始终发送信号，让窗口组件处理页面切换
                        control.bottomItemClicked(bottomNavItem.index)
                    }
                }
            }
        }
    }
}
