// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../icons"
import "../data"
import "_internal"

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
    
    // ==================== Signals 信号 ====================
    signal itemClicked(int index, bool byUser)
    signal currentItemChanged(string key)

    // ==================== Public Methods 公开方法 ====================
    function setCurrentIndex(idx) {
        if (idx < 0 || idx >= items.length) return
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

    // ==================== Public Methods 公开方法 ====================
    function setCurrentItem(key) {
        for (var i = 0; i < items.length; i++) {
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
        items = items.concat([newItem])
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
    radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small
    color: Enums.stateColor.segmentedBg
    border.width: Enums.border.thin
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
        radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small
        visible: control.items.length > 0
        color: Enums.stateColor.segmentedSelected
        border.width: Enums.border.thin
        border.color: Enums.stateColor.segmentedSelectedBorder
        
        Behavior on x { NumberAnimation { duration: Enums.duration.normal; easing.type: Easing.OutCubic } }
        Behavior on width { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
    }
    
    // Bottom indicator with shared horizontal stretch behavior 统一基类的水平橡皮筋粘滞底部指示器
    SlidingIndicator {
        id: navIndicator
        orientation: Qt.Horizontal
        indicatorWidth: control.indicatorSize
        indicatorHeight: Enums.border.thick
        radius: Enums.radius.micro
        visible: control.showIndicator && control.items.length > 0
    }

    Timer {
        id: slideSyncTimer

        property bool candidateReady: false
        property real candidateX: 0
        property real candidateWidth: 0

        function schedule(shouldAnimate) {
            if (shouldAnimate) {
                stop()
                candidateReady = false
                control._updateSlidePosition(true)
                return
            }

            candidateReady = false
            restart()
        }

        interval: Enums.duration.tick
        onTriggered: {
            var item = repeater.itemAt(control.currentIndex)
            if (!item || typeof item.x !== "number") {
                // A valid model may briefly have no delegate while Repeater rebuilds
                // Repeater 重建期间，有效模型可能短暂没有对应 delegate
                if (control.currentIndex >= 0 && control.currentIndex < control.items.length) {
                    restart()
                    return
                }
                candidateReady = false
                control._updateSlidePosition(false)
                return
            }

            var nextCandidateX = segmentRow.x + item.x
            var nextCandidateWidth = item.width || 0
            if (!candidateReady
                    || candidateX !== nextCandidateX
                    || candidateWidth !== nextCandidateWidth) {
                candidateReady = true
                candidateX = nextCandidateX
                candidateWidth = nextCandidateWidth
                restart()
                return
            }

            candidateReady = false
            control._updateSlidePosition(false)
        }
    }
    
    // Items row 项目行
    Row {
        id: segmentRow
        anchors.centerIn: parent
        spacing: Enums.spacing.none
        onXChanged: slideSyncTimer.schedule(false)
        
        Repeater {
            id: repeater
            model: control.items
            
            Item {
                id: segmentItem
                property bool selected: index === control.currentIndex
                property bool hovered: hoverHandler.hovered
                property bool pressed: tapHandler.pressed
                property string itemText: modelData.text !== undefined ? modelData.text : (typeof modelData === "string" ? modelData : "")
                property string itemIcon: modelData.icon !== undefined ? modelData.icon : ""
                property string key: modelData.key !== undefined ? modelData.key : (itemText !== "" ? itemText : itemIcon)
                property bool hasIcon: itemIcon !== ""
                property bool hasText: itemText !== ""

                width: Math.max(Enums.controlSize.segmentedMinWidth, itemContent.implicitWidth + Enums.spacing.l * 2)
                height: control.height - Enums.spacing.xxs * 2
                onSelectedChanged: if (selected) slideSyncTimer.schedule(false)
                onWidthChanged: if (selected) slideSyncTimer.schedule(false)
                onXChanged: if (selected) slideSyncTimer.schedule(false)
                Component.onCompleted: if (selected) slideSyncTimer.schedule(false)
                
                // Hover/Press background for non-selected items 非选中项的悬停/按下背景
                Rectangle {
                    anchors.fill: parent
                    radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small
                    visible: !segmentItem.selected && (segmentItem.hovered || segmentItem.pressed)
                    color: {
                        if (segmentItem.pressed) return Enums.stateColor.segmentedPressed
                        if (segmentItem.hovered) return Enums.stateColor.segmentedHover
                        return Enums.transparent
                    }
                }
                
                // Content row (icon + text) 内容行
                Row {
                    id: itemContent
                    anchors.centerIn: parent
                    spacing: (segmentItem.hasIcon && segmentItem.hasText) ? Enums.spacing.s : 0
                    
                    Icon {
                        id: iconItem
                        icon: segmentItem.itemIcon
                        iconSize: control.iconSize
                        color: textItem.color
                        visible: segmentItem.hasIcon
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    Label {
                        id: textItem
                        type: Enums.label.type_body
                        text: segmentItem.itemText
                        font.pixelSize: control.itemFontSize
                        visible: segmentItem.hasText
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                
                // HoverHandler for stable hover 使用HoverHandler实现稳定hover
                HoverHandler {
                    id: hoverHandler
                    cursorShape: Qt.PointingHandCursor
                }
                
                // TapHandler for click 使用TapHandler处理点击
                TapHandler {
                    id: tapHandler
                    onTapped: {
                        if (index !== control.currentIndex) {
                            control.setCurrentIndex(index)
                            control.itemClicked(index, true)
                        }
                    }
                }
            }
        }
    }
}
