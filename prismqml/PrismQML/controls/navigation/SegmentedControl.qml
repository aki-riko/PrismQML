// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal" as NavigationInternal

// SegmentedControl - Segmented control with icon+text support 分段控件
// Uses HoverHandler to provide stable hover behavior 使用HoverHandler提供稳定的悬停行为
Rectangle {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var items: []
    property int currentIndex: 0
    property int indicatorSize: Enums.controlSize.navIndicatorHeight
    property int itemFontSize: Enums.typography.body
    property int iconSize: Enums.iconSize.m
    property bool showIndicator: true

    // ==================== Internal Props 内部属性 ====================
    property real _slideX: 0
    property int _selectedItemWidth: Enums.controlSize.segmentedMinWidth
    property int _selectedItemHeight: height - Enums.spacing.xxs * 2
    readonly property var _safeItems:
        items === null || items === undefined ? []
        : (typeof items.length === "number" ? items : [])
    
    // ==================== Signals 信号 ====================
    signal itemClicked(int index, bool byUser)
    signal currentItemChanged(string key)

    // ==================== Public Methods 公开方法 ====================
    function setCurrentIndex(idx) {
        if (idx < 0 || idx >= _safeItems.length) return
        if (idx === currentIndex) return

        // Only update the index; one handler drives geometry to avoid duplicate interruption 只修改索引，由统一handler驱动几何以免双发打断动画
        currentIndex = idx

        var item = repeater.itemAt(idx)
        if (item) currentItemChanged(item.key)
    }

    // ==================== Internal Methods 内部方法 ====================
    // Center the bottom indicator in the selected item 底部指示器居中于选中项
    function _indicatorRect() {
        return Qt.rect(_slideX + (_selectedItemWidth - indicatorSize) / 2,
                       control.height - 3.5,
                       indicatorSize,
                       Enums.border.thick)
    }

    function _updateSlidePosition(animate) {
        var item = repeater.itemAt(currentIndex)
        if (!item || typeof item.x !== "number") {
            navIndicator.stopAnimation()
            return
        }
        var startRect = navIndicator.getIndicatorRect()
        var nextSlideX = segmentRow.x + item.x
        var nextItemWidth = item.width || 0
        _slideX = nextSlideX
        _selectedItemWidth = nextItemWidth
        _selectedItemHeight = (item.height || 0) + Enums.spacing.xxs * 2
        var endRect = _indicatorRect()
        if ((animate || navIndicator.running) && navIndicator._initialized) {
            navIndicator.startAnimation(startRect, endRect)
        } else {
            navIndicator.setGeometry(endRect)
        }
    }

    function _scheduleSlideSync(shouldAnimate) {
        slideSyncTimer.schedule(shouldAnimate)
    }

    // ==================== Public Methods 公开方法 ====================
    function setCurrentItem(key) {
        for (var i = 0; i < _safeItems.length; i++) {
            var item = repeater.itemAt(i)
            if (item && item.key === key) {
                setCurrentIndex(i)
                return
            }
        }
    }

    // Add item 添加项目
    function addItem(key, text, icon) {
        var newItem = { key: key, text: text, icon: icon || "" }
        items = _safeItems.concat([newItem])
    }

    // Get current page key 获取当前页面键
    function getCurrentKey() {
        var item = repeater.itemAt(currentIndex)
        return item ? item.key : ""
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: segmentRow.implicitWidth + Enums.spacing.xs * 2
    implicitHeight: Enums.controlSize.segmentedHeight

    // Background 背景
    radius: Enums.surfaceRadius(Enums.radius.small)
    color: Enums.stateColor.segmentedBg
    border.width: Enums.surfaceBorderWidth(Enums.border.thin)
    border.color: Enums.stateColor.segmentedBorder

    Component.onCompleted: slideSyncTimer.schedule(false)
    onItemsChanged: slideSyncTimer.schedule(false)
    onWidthChanged: slideSyncTimer.schedule(false)
    onCurrentIndexChanged: slideSyncTimer.schedule(true)

    // ==================== Content 内容 ====================
    Rectangle {
        id: selectedBg
        x: control._slideX
        y: Enums.spacing.xxs
        width: control._selectedItemWidth
        height: control.height - Enums.spacing.xxs * 2
        radius: Enums.surfaceRadius(Enums.radius.small)
        visible: control._safeItems.length > 0
        color: Enums.stateColor.segmentedSelected
        border.width: Enums.surfaceBorderWidth(Enums.border.thin)
        border.color: Enums.stateColor.segmentedSelectedBorder
        
        Behavior on x { NumberAnimation { duration: Enums.duration.normal; easing.type: Easing.OutCubic } }
        Behavior on width { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
    }
    
    // Bottom indicator with shared horizontal stretch behavior 统一基类的水平橡皮筋粘滞底部指示器
    NavigationInternal.SlidingIndicator {
        id: navIndicator
        orientation: Qt.Horizontal
        indicatorWidth: control.indicatorSize
        indicatorHeight: Enums.border.thick
        radius: Enums.radius.micro
        visible: control.showIndicator && control._safeItems.length > 0
    }

    NavigationInternal.SegmentedSlideSyncTimer {
        id: slideSyncTimer

        host: control
        segmentRow: segmentRow
        itemRepeater: repeater
    }
    
    // Items row 项目行
    Row {
        id: segmentRow
        anchors.centerIn: parent
        spacing: Enums.spacing.none
        onXChanged: slideSyncTimer.schedule(false)
        
        Repeater {
            id: repeater
            model: control._safeItems
            
            NavigationInternal.SegmentedItem {
                segmentedControl: control
            }
        }
    }
}
