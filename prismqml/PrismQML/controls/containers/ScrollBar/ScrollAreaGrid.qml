// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../../.."
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ScrollAreaGrid - Virtualized grid scroll area 虚拟化网格滚动区域
// Only renders visible items 只渲染可见项
// Refactored to use SmoothScrollHelper 重构为使用SmoothScrollHelper
Item {
    id: control
    
    // ==================== Props 属性 ====================
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
    
    // ==================== Expose props 暴露属性 ====================
    property alias contentY: gridView.contentY
    property alias contentHeight: gridView.contentHeight
    readonly property alias gridView: gridView
    readonly property int count: gridView.count
    
    // ==================== Signals 信号 ====================
    signal itemClicked(int index, var item)
    signal indexChanged(int index)

    // ==================== Public Methods 公开方法 ====================
    function scrollToTop() { scrollHelper.scrollToStart() }
    function scrollToBottom() { scrollHelper.scrollToEnd() }
    function smoothScrollTo(targetY) { scrollHelper.scrollTo(targetY) }
    function smoothScrollBy(delta) { scrollHelper.scrollBy(delta) }

    // ==================== GridView 网格视图 ====================
    GridView {
        id: gridView
        anchors.fill: parent
        anchors.rightMargin: showScrollBar && contentHeight > height ? scrollBarWidth + Enums.spacing.xs : 0
        
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
    
    Component {
        id: highlightComp
        Rectangle {
            color: Enums.stateColor.accentLight
            radius: Enums.radius.small
        }
    }
    
    // ==================== Smooth Scroll Helper 平滑滚动助手 ====================
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
    
    // ==================== Scrollbar 滚动条 ====================
    ScrollBar {
        id: vBar
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: Enums.spacing.xxs
        
        target: gridView
        scrollHelper: scrollHelper
        orientation: Qt.Vertical
        barWidth: scrollBarWidth
        visible: showScrollBar && gridView.contentHeight > gridView.height
    }
}
