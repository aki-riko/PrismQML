// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ScrollAreaGrid - Virtualized grid scroll area 虚拟化网格滚动区域
// Only renders visible items 只渲染可见项
// Refactored to use SmoothScrollHelper 重构为使用SmoothScrollHelper
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var model: []
    property Component delegate: null
    property int cellWidth: 100
    property int cellHeight: 100
    // delegate 复用 (Qt 5.15+): 大 model 滚动时避免反复 create/destroy delegate,
    // 是网格流畅滚动的关键。grid 几乎总是大数据场景, 默认开启。
    // delegate 为纯展示(仅绑 modelData)时安全; 若 delegate 含内部可变状态需自行在
    // GridView.onReused 中重置, 或将本属性置 false。
    property bool reuseItems: true
    property int cacheBuffer: -1  // -1 = 用默认 cellHeight*5
    property bool showScrollBar: true
    property int scrollBarWidth: Enums.controlSize.scrollBarWidth
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    property int currentIndex: -1
    property bool selectable: true
    
    // Exposed aliases 暴露别名
    property alias contentY: gridView.contentY
    property alias contentHeight: gridView.contentHeight

    // ==================== Readonly State 只读状态 ====================
    readonly property alias gridView: gridView
    readonly property int count: gridView.count
    readonly property alias _needsScrollBar: scrollViewportState.needsVertical
    readonly property alias _reserveScrollBarGutter:
        scrollViewportState.reserveVerticalGutter
    readonly property real _scrollBarGutter:
        Math.max(0, scrollBarWidth) + Enums.spacing.xs
    
    // ==================== Signals 信号 ====================
    signal itemClicked(int index, var item)
    signal indexChanged(int index)

    // ==================== Public Methods 公开方法 ====================
    function scrollToTop() { scrollHelper.scrollToStart() }
    function scrollToBottom() { scrollHelper.scrollToEnd() }
    function smoothScrollTo(targetY) { scrollHelper.scrollTo(targetY) }
    function smoothScrollBy(delta) { scrollHelper.scrollBy(delta) }

    // ==================== Internal Methods 内部方法 ====================
    function _scheduleScrollBarUpdate() {
        if (scrollViewportState) scrollViewportState.invalidate()
    }

    onWidthChanged: _scheduleScrollBarUpdate()
    onHeightChanged: _scheduleScrollBarUpdate()
    onCellWidthChanged: _scheduleScrollBarUpdate()
    onCellHeightChanged: _scheduleScrollBarUpdate()
    onScrollBarWidthChanged: _scheduleScrollBarUpdate()

    // ==================== Content 内容 ====================
    // Grid view 网格视图
    GridView {
        id: gridView
        anchors.fill: parent
        anchors.rightMargin: control._reserveScrollBarGutter
            ? Math.min(control._scrollBarGutter, Math.max(0, parent.width)) : 0
        
        model: control.model
        delegate: control.delegate
        cellWidth: control.cellWidth
        cellHeight: control.cellHeight
        clip: true
        interactive: false
        reuseItems: control.reuseItems
        cacheBuffer: control.cacheBuffer >= 0 ? control.cacheBuffer : cellHeight * 5
        currentIndex: control.currentIndex
        onCurrentIndexChanged: control.indexChanged(currentIndex)
        
        highlight: selectable ? highlightComp : null
        highlightFollowsCurrentItem: true
        highlightMoveDuration: Enums.duration.fast
    }

    ScrollViewportState {
        id: scrollViewportState
        target: gridView
        scrollBarsEnabled: control.showScrollBar
        verticalEnabled: true
        itemCount: gridView.count
    }
    
    Component {
        id: highlightComp
        Rectangle {
            color: Enums.stateColor.accentLight
            radius: Enums.radius.small
        }
    }
    
    // Smooth scroll helper 平滑滚动助手
    SmoothScrollHelper {
        id: scrollHelper
        target: gridView
        orientation: Qt.Vertical
        enabled: control.smoothScroll
        duration: control.scrollDuration
        step: control.scrollStep
        easing: control.scrollEasing
        bounceEnabled: true
        handleWheel: true
    }
    
    // Scrollbar 滚动条
    ScrollBar {
        id: vBar
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: Enums.spacing.xxs
        
        target: gridView
        scrollHelper: scrollHelper
        orientation: Qt.Vertical
        barWidth: Math.max(0, scrollBarWidth)
        visible: control._needsScrollBar
    }
}
