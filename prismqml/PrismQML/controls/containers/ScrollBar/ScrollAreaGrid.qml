// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import "../../data/List/_internal/collection"
import "../../data/List/_internal/RepeaterModel.js" as RepeaterModel
import QtQuick  // After library import: unprefixed native types stay unshadowed 置于库import后:去前缀后保原生类型不被库覆盖

// ScrollAreaGrid - Virtualized grid scroll area 虚拟化网格滚动区域
// Only renders visible items 只渲染可见项
// Refactored to use SmoothScrollHelper 重构为使用SmoothScrollHelper
// Selection (selectionMode) and incremental loading (incrementalLoadingEnabled) are
// opt-in: with their defaults the grid behaves and paints exactly as before.
// 选择 (selectionMode) 与增量加载 (incrementalLoadingEnabled) 均为可选: 使用默认值时
// 网格的行为与绘制与之前完全一致。
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
    property int cacheBuffer: -1  // -1 = default cellHeight*5 -1 = 用默认 cellHeight*5
    property bool showScrollBar: true
    property int scrollBarWidth: Enums.controlSize.scrollBarWidth
    property bool smoothScroll: true
    // Enable native touch/mouse drag scrolling 启用原生触摸/鼠标拖拽滚动
    property bool dragScrollEnabled: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    property int currentIndex: -1
    property bool selectable: true
    // Selection mode, Enums.scroll.selection_* 选择模式
    property int selectionMode: Enums.scroll.selection_none
    // Incremental loading 增量加载
    property bool incrementalLoadingEnabled: false
    // Rows before the content end that request the next batch 距内容末尾多少行时请求下一批
    property int incrementalLoadingThreshold: 3
    // Rows asked for in one loadMoreRequested 单次 loadMoreRequested 请求的行数
    property int incrementalLoadingBatchSize: 20
    
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
    readonly property var selectedIndexes: selection.selectedIndexes
    readonly property int selectedCount: selection.selectedCount
    readonly property bool isLoadingMore: incrementalTrigger.isLoading
    readonly property bool _selectionActive:
        control.selectionMode !== Enums.scroll.selection_none
    
    // ==================== Signals 信号 ====================
    signal itemClicked(int index, var item)
    signal indexChanged(int index)
    signal selectionChanged()
    signal loadMoreRequested(int batchSize)

    // ==================== Public Methods 公开方法 ====================
    function scrollToTop() { scrollHelper.scrollToStart() }
    function scrollToBottom() { scrollHelper.scrollToEnd() }
    function smoothScrollTo(targetY) { scrollHelper.scrollTo(targetY) }
    function smoothScrollBy(delta) { scrollHelper.scrollBy(delta) }
    function selectIndex(index, selected) { selection.selectIndex(index, selected) }
    function clearSelection() { selection.clear() }
    function selectAll() { selection.selectAll() }
    function isSelected(index) { return selection.isSelected(index) }

    // Model data of every selected index, ascending 所有选中索引的模型数据, 升序
    function selectedItems() {
        var indexes = selection.selectedIndexes
        var items = []
        for (var cursor = 0; cursor < indexes.length; ++cursor) {
            items.push(RepeaterModel.dataAt(control.model, indexes[cursor]))
        }
        return items
    }

    // Consumer signals the requested batch has been appended 消费方通知所请求批次已追加
    function completeIncrementalLoad() { incrementalTrigger.complete() }

    // ==================== Internal Methods 内部方法 ====================
    function _scheduleScrollBarUpdate() {
        if (scrollViewportState) scrollViewportState.invalidate()
    }

    function _handleGridTap(index, modifiers) {
        if (index < 0) return
        control.currentIndex = index
        selection.handleClick(index, modifiers)
        control.itemClicked(index, RepeaterModel.dataAt(control.model, index))
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
        interactive: control.dragScrollEnabled
        reuseItems: control.reuseItems
        cacheBuffer: control.cacheBuffer >= 0 ? control.cacheBuffer : cellHeight * 5
        currentIndex: control.currentIndex
        onCurrentIndexChanged: control.indexChanged(currentIndex)
        
        highlight: selectable ? highlightComp : null
        highlightFollowsCurrentItem: true
        highlightMoveDuration: Enums.duration.fast

        // Selection layer. It is declared inside the view so it stays a descendant of
        // the flickable and cannot block drag scrolling, and it exists only while a
        // selection mode is active.
        // 选择层声明在视图内部, 保持为 flickable 的后代, 不会阻断拖拽滚动;
        // 只有选择模式激活时才存在。
        Loader {
            id: selectionLayer
            parent: gridView.contentItem
            width: Math.max(gridView.contentWidth, gridView.width)
            height: Math.max(gridView.contentHeight, gridView.height)
            z: Enums.zIndex.content
            active: control._selectionActive
            sourceComponent: selectionLayerComponent
        }
    }

    ScrollViewportState {
        id: scrollViewportState
        target: gridView
        scrollBarsEnabled: control.showScrollBar
        verticalEnabled: true
        itemCount: gridView.count
    }

    // Selection state 选择状态
    CollectionSelection {
        id: selection
        mode: control.selectionMode
        itemCount: gridView.count
        onSelectionChanged: control.selectionChanged()
    }

    // Incremental loading gate 增量加载门
    IncrementalLoadTrigger {
        id: incrementalTrigger
        viewport: gridView
        enabled: control.incrementalLoadingEnabled
        itemCount: gridView.count
        batchSize: control.incrementalLoadingBatchSize
        triggerDistance: Math.max(0, control.incrementalLoadingThreshold)
            * Math.max(0, control.cellHeight)
        onLoadRequested: (batchSize) => control.loadMoreRequested(batchSize)
    }
    
    Component {
        id: highlightComp
        Rectangle {
            color: Enums.stateColor.accentLight
            radius: Enums.radius.small
        }
    }

    // Selection layer content 选择层内容
    Component {
        id: selectionLayerComponent
        Item {
            // Selection chrome 选择底板
            Repeater {
                model: control.selectedIndexes

                Rectangle {
                    // Live delegate of the selected index, re-read on every scroll
                    // 选中索引的存活委托, 每次滚动重新读取
                    readonly property var _item: {
                        gridView.contentY
                        gridView.count
                        return gridView.itemAtIndex(modelData)
                    }
                    x: _item ? _item.x : 0
                    y: _item ? _item.y : 0
                    width: _item ? _item.width : 0
                    height: _item ? _item.height : 0
                    visible: _item !== null && _item !== undefined
                    color: Enums.stateColor.accentLight
                    border.width: Enums.border.thin
                    border.color: Enums.stateColor.accentBorder
                    radius: Enums.radius.small
                }
            }

            // Tap layer 点击层
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton
                onClicked: function(mouse) {
                    control._handleGridTap(
                        gridView.indexAt(mouse.x, mouse.y), mouse.modifiers)
                }
            }
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
