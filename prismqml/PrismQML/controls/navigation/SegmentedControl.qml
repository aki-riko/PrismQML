// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal" as NavigationInternal

// SegmentedControl - Segmented control with icon+text support 分段控件
// Uses HoverHandler to provide stable hover behavior 使用HoverHandler提供稳定的悬停行为
// orientation picks the main axis; Qt.Horizontal behaves exactly as before
// orientation 选择主轴; Qt.Horizontal 与之前完全一致
Rectangle {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var items: []
    property int currentIndex: 0
    property int indicatorSize: Enums.controlSize.navIndicatorHeight
    property int itemFontSize: Enums.typography.body
    property int iconSize: Enums.iconSize.m
    property bool showIndicator: true
    property int orientation: Qt.Horizontal

    // ==================== Internal Props 内部属性 ====================
    property real _slideX: 0
    property real _slideY: 0
    property int _selectedItemWidth: Enums.controlSize.segmentedMinWidth
    property int _selectedItemHeight: 0
    readonly property bool vertical: orientation === Qt.Vertical
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
    // Indicator rect; the cross axis follows the strip, the main axis keeps the
    // historical geometry. 指示器矩形; 副轴跟随条带, 主轴保持历史几何。
    function _indicatorRect() {
        if (vertical) {
            return Qt.rect(_slideX,
                           _slideY + (_selectedItemHeight - indicatorSize) / 2,
                           Enums.border.thick, indicatorSize)
        }
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
        _slideX = segmentRow.x + item.x
        _slideY = segmentRow.y + item.y
        _selectedItemWidth = item.width || 0
        _selectedItemHeight = item.height || 0
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
    implicitHeight: vertical
        ? segmentRow.implicitHeight + Enums.spacing.xxs * 2
        : Enums.controlSize.segmentedHeight

    // Background 背景
    radius: Enums.surfaceRadius(Enums.radius.small)
    color: Enums.stateColor.segmentedBg
    border.width: Enums.surfaceBorderWidth(Enums.border.thin)
    border.color: Enums.stateColor.segmentedBorder

    Component.onCompleted: slideSyncTimer.schedule(false)
    onItemsChanged: slideSyncTimer.schedule(false)
    onWidthChanged: slideSyncTimer.schedule(false)
    onOrientationChanged: slideSyncTimer.schedule(false)
    onCurrentIndexChanged: slideSyncTimer.schedule(true)

    // ==================== Content 内容 ====================
    NavigationInternal.SegmentedSelectedBackground {
        id: selectedBg
        host: control
    }

    // Shared sliding indicator; it already owns both axes 统一滑动指示器; 本身已支持双轴
    NavigationInternal.SlidingIndicator {
        id: navIndicator
        orientation: control.orientation
        indicatorWidth: control.vertical ? Enums.border.thick : control.indicatorSize
        indicatorHeight: control.vertical ? control.indicatorSize : Enums.border.thick
        radius: Enums.radius.micro
        visible: control.showIndicator && control._safeItems.length > 0
    }

    NavigationInternal.SegmentedSlideSyncTimer {
        id: slideSyncTimer

        host: control
        segmentRow: segmentRow
        itemRepeater: repeater
    }

    // Items strip; Flow switches the main axis without a second delegate tree
    // 项目条带; Flow 切换主轴, 无需第二棵委托树
    Flow {
        id: segmentRow
        flow: control.vertical ? Flow.TopToBottom : Flow.LeftToRight
        anchors.centerIn: parent
        spacing: Enums.spacing.none
        onXChanged: slideSyncTimer.schedule(false)
        onYChanged: slideSyncTimer.schedule(false)

        Repeater {
            id: repeater
            model: control._safeItems

            NavigationInternal.SegmentedItem {
                segmentedControl: control
            }
        }
    }
}
