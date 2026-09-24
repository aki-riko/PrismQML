// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal"

// Pivot - Pivot navigation component 透视导航组件
// Uses Button to provide stable hover behavior 使用Button提供稳定的悬停行为
// orientation picks the main axis; Qt.Horizontal behaves exactly as before
// orientation 选择主轴; Qt.Horizontal 与之前完全一致
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var items: []
    property int currentIndex: 0
    property int indicatorSize: Enums.controlSize.navIndicatorHeight
    property int itemFontSize: Enums.typography.subtitle
    property int iconSize: Enums.iconSize.m
    property bool indicatorAnimationEnabled: true
    property int orientation: Qt.Horizontal

    // ==================== Internal Props 内部属性 ====================
    property int _prevIndex: -1
    property bool _initialized: false
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
        if (idx === currentIndex) {
            if (!_initialized) _updateIndicatorWithAnimation()
            return
        }

        // Only update the index; one handler drives geometry to avoid duplicate interruption 只修改索引，由统一handler驱动几何以免双发打断动画
        currentIndex = idx

        var item = repeater.itemAt(idx)
        if (item) currentItemChanged(item.key)
    }

    // ==================== Internal Methods 内部方法 ====================
    // Indicator rect; vertical pins the bar to the item's left edge while the
    // horizontal treatment keeps the historical bottom underline.
    // 指示器矩形; 纵向时竖条贴项的左边缘, 横向保持历史的下划线几何。
    function _rectAt(item) {
        if (!item) return Qt.rect(0, 0, 0, 0)
        if (vertical) {
            return Qt.rect(item.x,
                           item.y + (item.height - indicatorSize) / 2,
                           Enums.border.thick,
                           indicatorSize)
        }
        return Qt.rect(item.x + (item.width - indicatorSize) / 2,
                       control.height - Enums.border.thick,
                       indicatorSize,
                       Enums.border.thick)
    }

    function _updateIndicatorWithAnimation() {
        var newItem = repeater.itemAt(currentIndex)
        if (!newItem) {
            if (currentIndex >= 0 && currentIndex < _safeItems.length) {
                // A valid model may briefly have no delegate while Repeater rebuilds
                // Repeater重建期间合法索引可能暂时没有delegate，延后一帧重试
                if (!indicatorSyncTimer.running) indicatorSyncTimer.restart()
                return
            }
            // Drop stale geometry while selection is invalid
            // 选择真实失效时撤销旧几何，避免指示器停在错误项目
            indicatorSyncTimer.stop()
            navIndicator.stopAnimation()
            _initialized = false
            _prevIndex = -1
            return
        }
        indicatorSyncTimer.stop()

        var endRect = _rectAt(newItem)

        if (!_initialized) {
            navIndicator.setGeometry(endRect)
            _initialized = true
            _prevIndex = currentIndex
            return
        }

        if (!indicatorAnimationEnabled || _prevIndex === currentIndex) {
            navIndicator.setGeometry(endRect)
            _prevIndex = currentIndex
            return
        }

        var prevItem = repeater.itemAt(_prevIndex)
        if (prevItem) {
            // Retarget from the rendered frame instead of the previous destination
            // 连续切换时从当前渲染帧改道，避免瞬跳到上一个目标位置
            var startRect = navIndicator.running
                ? navIndicator.getIndicatorRect() : _rectAt(prevItem)
            navIndicator.startAnimation(startRect, endRect)
        } else {
            navIndicator.setGeometry(endRect)
        }

        _prevIndex = currentIndex
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
    implicitWidth: pivotRow.implicitWidth
    implicitHeight: vertical
        ? pivotRow.implicitHeight
        : Enums.controlSize.inputHeight

    Component.onCompleted: indicatorSyncTimer.restart()
    onItemsChanged: indicatorSyncTimer.restart()
    onCurrentIndexChanged: _updateIndicatorWithAnimation()
    onOrientationChanged: indicatorSyncTimer.restart()
    onWidthChanged: {
        if (_initialized && !navIndicator.running) {
            var item = repeater.itemAt(currentIndex)
            if (item) navIndicator.setGeometry(_rectAt(item))
        }
    }

    // ==================== Content 内容 ====================
    // Items strip; Flow switches the main axis without a second delegate tree
    // 项目条带; Flow 切换主轴, 无需第二棵委托树
    Flow {
        id: pivotRow
        flow: control.vertical ? Flow.TopToBottom : Flow.LeftToRight
        // Horizontal keeps filling the control (historical geometry). Vertical must
        // stay unanchored: constraining a positioner's own size on the main axis makes
        // its implicit size depend on that size, and the stack then wraps into columns.
        // 横向保持填满控件（历史几何）。纵向必须不锚定: 在主轴上约束 positioner 自身
        // 尺寸会让其隐式尺寸依赖该尺寸, 堆叠随即退化成多列。
        anchors.fill: control.vertical ? undefined : parent
        spacing: Enums.spacing.none
        
        Repeater {
            id: repeater
            model: control._safeItems
            
            PivotItem {
                host: control
            }
        }
    }
    
    // Shared sticky-stretch indicator; it already owns both axes 统一粘滞指示器; 本身已支持双轴
    SlidingIndicator {
        id: navIndicator
        orientation: control.orientation
        indicatorWidth: control.vertical ? Enums.border.thick : control.indicatorSize
        indicatorHeight: control.vertical ? control.indicatorSize : Enums.border.thick
        radius: Enums.radius.micro
        animationEnabled: control.indicatorAnimationEnabled
        visible: control._safeItems.length > 0 && control._initialized
    }

    PivotIndicatorSyncTimer {
        id: indicatorSyncTimer

        host: control
    }

}
