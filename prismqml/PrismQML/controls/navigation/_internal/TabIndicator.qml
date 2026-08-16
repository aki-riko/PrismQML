// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."
import "../../../effects"

// TabIndicator - Selected-tab indicator rendering and geometry synchronization
// TabIndicator - 选中标签指示器绘制与几何同步
Item {
    id: slidingIndicator

    // ==================== Required Props 必需属性 ====================
    required property Item host
    required property Item tabBar
    required property Flickable tabFlickable
    required property var tabRepeater
    required property Item tabRow

    // ==================== Internal Props 内部属性 ====================
    // itemAt() is not reactive, so delegate changes explicitly bump this key.
    // itemAt() 不具响应性，因此委托变化时显式递增此键。
    property int _currentTabKey: 0
    property Item currentTab: {
        var _ = _currentTabKey
        return (tabRepeater.count > 0 && host.currentIndex >= 0 &&
                host.currentIndex < tabRepeater.count)
               ? tabRepeater.itemAt(host.currentIndex) : null
    }
    // Preserve engine geometry while selection or model sync is pending.
    // 选择切换或模型同步待处理时保留引擎几何。
    property real tabLocalX: (
        _eng.running || !currentTab || _syncedIndex !== host.currentIndex ||
        _syncedTab !== currentTab) ? _eng.indicatorX : currentTab.x
    property real targetWidth: (
        _eng.running || !currentTab || _syncedIndex !== host.currentIndex ||
        _syncedTab !== currentTab) ? _eng.indicatorWidth : currentTab.width
    // Derive drag displacement from host state so the binding stays reactive.
    // 从宿主状态推导拖拽位移，确保绑定保持响应。
    property real tabVisualOffsetX: {
        if (!host._dragging) return 0
        var src = host._dragSourceIndex
        var vis = host._dragVisualIndex
        var cur = host.currentIndex
        if (cur === src) return host._dragSourceOffsetX
        var w = currentTab ? currentTab.width : 0
        if (src < vis) {
            if (cur > src && cur <= vis) return -w
        } else if (src > vis) {
            if (cur >= vis && cur < src) return w
        }
        return 0
    }
    property real scrollOffset: tabFlickable.contentX
    property real targetX: tabFlickable.x + tabLocalX + tabVisualOffsetX -
                           scrollOffset + Enums.border.thin
    property real targetY: tabFlickable.y - tabBar.y + Enums.border.thin
    property real targetHeight: currentTab
        ? currentTab.height - Enums.spacing.xxs
        : Enums.controlSize.inputHeightLarge - Enums.spacing.s
    property bool _engInit: false
    property int _syncedIndex: -1
    property Item _syncedTab: null
    property real _layoutX: currentTab ? currentTab.x : 0
    property real _layoutW: currentTab
        ? currentTab.width : Enums.controlSize.segmentedMinWidth

    // ==================== Internal Methods 内部方法 ====================
    function _curRect() {
        var tab = currentTab
        return tab ? Qt.rect(tab.x, 0, tab.width, 1) : null
    }

    function _engineRect() {
        return Qt.rect(_eng.indicatorX, 0, _eng.indicatorWidth, 1)
    }

    function _scheduleSync(animate) {
        // Freeze the interpolated frame before the zero-delay layout sync.
        // 在零延迟布局同步前冻结当前插值帧，避免旧目标再提交一帧。
        if (animate && _eng.running && _syncedIndex !== host.currentIndex) {
            _eng.stopAnimation()
        }
        _syncTimer.animate = _syncTimer.animate || animate
        _syncTimer.restart()
    }

    function _runScheduledSync() {
        var animate = _syncTimer.animate
        _syncTimer.animate = false
        if (!currentTab || !_engInit) {
            syncIndicator(false)
            return
        }
        if (animate && _syncedIndex !== host.currentIndex) {
            syncIndicator(true)
            return
        }
        if (_syncedIndex === host.currentIndex) _followLayout()
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
        if (animate && _engInit && _syncedIndex !== host.currentIndex) {
            _eng.animateTo(_engineRect(), endRect)
        } else if (!_eng.running) {
            _eng.setGeometry(endRect)
        }
        _engInit = true
        _syncedIndex = host.currentIndex
        _syncedTab = currentTab
    }

    function _followLayout() {
        if (!currentTab || !_engInit ||
                _syncedIndex !== host.currentIndex) return
        // Flush the Row after delegate replacement before reading geometry.
        // 委托替换后先刷新 Row，再读取最终几何，避免瞬态 x=0 触发反向重定向。
        tabRow.forceLayout()
        var rect = _curRect()
        if (!rect) return
        _syncedTab = currentTab
        if (_eng.running) _eng.animateTo(_engineRect(), rect)
        else _eng.setGeometry(rect)
    }

    // ==================== Size 尺寸 ====================
    // The dragged source renders its selected background itself.
    // 拖动源自身绘制选中背景，拖动期间隐藏原指示器以避免鬼影。
    visible: tabRepeater.count > 0 && currentTab && _engInit && !host._dragging
    x: targetX
    y: targetY
    width: targetWidth
    height: targetHeight
    onCurrentTabChanged: _scheduleSync(false)
    Component.onCompleted: _scheduleSync(false)
    on_LayoutXChanged: _scheduleSync(false)
    on_LayoutWChanged: _scheduleSync(false)

    // ==================== Content 内容 ====================
    // Horizontal stretch engine driving tabLocalX and targetWidth.
    // 水平橡皮筋引擎驱动 tabLocalX 与 targetWidth。
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

    RectangularShadow {
        anchors.fill: indicatorBg
        radius: indicatorBg.radius
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset.x: 0
        offset.y: Enums.shadow.level2.offset
        visible: host.shadowEnabled && Enums.usesSoftElevation &&
                 !Enums.isNeumorphism
    }

    NeumorphicShadow {
        target: indicatorBg
        inset: true
        visible: host.shadowEnabled && Enums.isNeumorphism
        z: indicatorBg.z - 1
    }

    NeoShadow {
        target: indicatorBg
        visible: host.shadowEnabled && Enums.isNeobrutalism
        z: indicatorBg.z - 1
    }

    Rectangle {
        id: indicatorBg
        anchors.fill: parent
        radius: host._selectedTabRadius
        color: Enums.hasOutlinedSurfaces || Enums.isNeumorphism
               ? Enums.cardColor
               : (Enums.isDark ? Enums.themeColors.tabSelectedDark
                               : Enums.themeColors.tabSelectedLight)
        border.width: host._selectedTabBorderWidth
        border.color: Enums.hasOutlinedSurfaces ? Enums.borderColor
                      : (Enums.isDark ? Enums.stateColor.borderLight
                                      : Enums.stateColor.border)
    }
}
