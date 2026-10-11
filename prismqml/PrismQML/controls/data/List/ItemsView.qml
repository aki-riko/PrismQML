// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal"
import "_internal/collection"
import "_internal/RepeaterModel.js" as RepeaterModel

// ItemsView - Collection view with selection and incremental loading 带选择与增量加载的集合视图
// Selection modes 选择模式: Enums.scroll.selection_none / selection_single /
// selection_multiple / selection_extended. Extended mode follows the platform
// convention: plain click replaces, Ctrl+click toggles, Shift+click extends the
// range from the anchor.
// 扩展模式遵循平台惯例: 普通点击替换, Ctrl+点击切换, Shift+点击从锚点扩展区间。
// Incremental loading 增量加载: when incrementalLoadingEnabled is true the view raises
// loadMoreRequested(batchSize) as soon as the viewport gets within
// incrementalLoadingThreshold rows of the end, then stays quiet until the consumer
// calls completeIncrementalLoad().
// 增量加载: 启用后视口进入末尾 incrementalLoadingThreshold 行内时发出
// loadMoreRequested(batchSize), 之后保持静默直到消费方调用 completeIncrementalLoad()。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var model: []
    property Component delegate: null
    property var layout: null
    property bool reuseItems: true
    property int cacheBuffer: -1
    property int selectionMode: Enums.scroll.selection_none
    property bool showScrollBar: true
    property int scrollBarWidth: Enums.controlSize.scrollBarWidth
    property bool smoothScroll: true
    property bool dragScrollEnabled: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    property bool bounceEnabled: true
    // Selection chrome colour 选择底板颜色
    property color selectionChromeColor: Enums.stateColor.selected
    property bool incrementalLoadingEnabled: false
    // Rows before the content end that request the next batch 距内容末尾多少行时请求下一批
    property int incrementalLoadingThreshold: 3
    // Rows asked for in one loadMoreRequested 单次 loadMoreRequested 请求的行数
    property int incrementalLoadingBatchSize: 20
    property alias currentIndex: repeater.currentIndex

    // ==================== Readonly State 只读状态 ====================
    readonly property int count: repeater.count
    // Main-axis size of one item 单个项目的主轴尺寸
    readonly property real itemExtent: repeater.itemExtent
    readonly property var selectedIndexes: selection.selectedIndexes
    readonly property int selectedCount: selection.selectedCount
    readonly property bool isLoadingMore: incrementalTrigger.isLoading
    readonly property int instantiatedCount: repeater.instantiatedCount
    readonly property int selectionChromeCount: repeater.selectionChromeCount
    readonly property int recycledCount: repeater.recycledCount
    readonly property alias flickableItem: repeater.flickableItem
    readonly property alias contentX: repeater.contentX
    readonly property alias contentY: repeater.contentY
    readonly property alias contentWidth: repeater.contentWidth
    readonly property alias contentHeight: repeater.contentHeight

    // ==================== Signals 信号 ====================
    signal itemClicked(int index, var item)
    signal indexChanged(int index)
    signal selectionChanged()
    signal loadMoreRequested(int batchSize)

    // ==================== Public Methods 公开方法 ====================
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
    function scrollToIndex(index) { repeater.scrollToIndex(index) }
    function scrollToTop() { repeater.scrollToTop() }
    function scrollToBottom() { repeater.scrollToBottom() }
    function smoothScrollTo(position) { repeater.smoothScrollTo(position) }
    function smoothScrollBy(delta) { repeater.smoothScrollBy(delta) }
    function itemAt(index) { return repeater.itemAt(index) }
    function indexAt(x, y) { return repeater.indexAt(x, y) }

    activeFocusOnTab: true
    Keys.onPressed: function(event) {
        if (control.selectionMode === Enums.scroll.selection_none) return
        if (event.matches(StandardKey.SelectAll)) {
            control.selectAll()
            event.accepted = true
        } else if (event.key === Qt.Key_Escape) {
            control.clearSelection()
            event.accepted = true
        }
    }

    // ==================== Content 内容 ====================
    // Selection state 选择状态
    CollectionSelection {
        id: selection
        mode: control.selectionMode
        itemCount: control.count
        onSelectionChanged: control.selectionChanged()
    }

    // Incremental loading gate 增量加载门
    IncrementalLoadTrigger {
        id: incrementalTrigger
        // The viewport alias only resolves once the view subtree exists, and an alias
        // to a not-yet-created object is not re-evaluated on its own.
        // 视口别名只有在视图子树就绪后才能解析, 而指向尚未创建对象的别名不会自行重算。
        viewport: repeater.ready ? repeater.flickableItem : null
        enabled: control.incrementalLoadingEnabled
        itemCount: control.count
        batchSize: control.incrementalLoadingBatchSize
        triggerDistance: Math.max(0, control.incrementalLoadingThreshold)
            * Math.max(0, repeater.itemExtent)
        onLoadRequested: (batchSize) => control.loadMoreRequested(batchSize)
    }

    // Virtualized host 虚拟化宿主
    ItemsRepeater {
        id: repeater
        anchors.fill: parent
        model: control.model
        delegate: control.delegate
        layout: control.layout
        reuseItems: control.reuseItems
        cacheBuffer: control.cacheBuffer
        interactive: true
        selectionController: selection
        selectionChromeColor: control.selectionChromeColor
        showScrollBar: control.showScrollBar
        scrollBarWidth: control.scrollBarWidth
        smoothScroll: control.smoothScroll
        dragScrollEnabled: control.dragScrollEnabled
        scrollDuration: control.scrollDuration
        scrollStep: control.scrollStep
        scrollEasing: control.scrollEasing
        bounceEnabled: control.bounceEnabled
        onItemClicked: (index, item) => control.itemClicked(index, item)
        onIndexChanged: (index) => control.indexChanged(index)
    }
}
