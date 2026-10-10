// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal"

// ItemsRepeater - Virtualized repeater with a pluggable layout 可插拔布局的虚拟化重复器
// Only the indices inside the layout's visible range hold a live delegate, and
// recycled delegates are reused instead of recreated while reuseItems is true.
// 只有布局可见范围内的索引持有存活委托; reuseItems 为真时回收复用而不是反复创建。
// Delegate contract 委托契约: declare `required property int index` and
// `required property var modelData`. The layout owns the delegate geometry.
// 委托契约: 必须声明 `required property int index` 与 `required property var modelData`;
// 委托的位置与尺寸由布局接管。
// Layout contract 布局契约: pass any ItemsRepeaterLayout-derived object as `layout`.
// 布局契约: 把任意派生自 ItemsRepeaterLayout 的对象传给 `layout`。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var model: []
    property Component delegate: null
    // Pluggable layout; null uses the built-in vertical stack 可插拔布局; null 使用内置纵向堆叠
    property var layout: null
    property bool reuseItems: true
    // -1 = two item extents of overscan -1 = 两个项目尺寸的预取
    property int cacheBuffer: -1
    // Report taps and move currentIndex; off keeps delegate input untouched
    // 上报点击并移动 currentIndex; 关闭时完全不触碰委托自身的输入
    property bool interactive: false
    property bool showScrollBar: true
    property int scrollBarWidth: Enums.controlSize.scrollBarWidth
    property bool smoothScroll: true
    property bool dragScrollEnabled: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    property bool bounceEnabled: true
    // Selection chrome colour, used when a selectionController is attached
    // 选择底板颜色, 仅在挂接 selectionController 时使用
    property color selectionChromeColor: Enums.stateColor.selected
    // Optional selection state object (see CollectionSelection) 可选的选择状态对象
    property var selectionController: null
    property alias currentIndex: core.currentIndex

    // ==================== Readonly State 只读状态 ====================
    readonly property var activeLayout:
        control.layout !== null ? control.layout : defaultLayout
    readonly property int count: core.count
    readonly property int instantiatedCount: core.instantiatedCount
    readonly property int selectionChromeCount: core.selectionChromeCount
    readonly property int recycledCount: core.recycledCount
    // True once the viewport exists 视口就绪后为真
    readonly property bool ready: core.ready
    // Main-axis size of one item, 0 when the layout is not ready
    // 单个项目的主轴尺寸, 布局未就绪时为 0
    readonly property real itemExtent: {
        var rect = control.activeLayout ? control.activeLayout.itemRect(0) : null
        if (!rect) return 0
        return control.activeLayout.scrollOrientation === Qt.Vertical
            ? rect.height : rect.width
    }
    readonly property alias flickableItem: core.flickableItem
    readonly property alias contentX: core.contentX
    readonly property alias contentY: core.contentY
    readonly property alias contentWidth: core.contentWidth
    readonly property alias contentHeight: core.contentHeight

    // ==================== Signals 信号 ====================
    signal itemClicked(int index, var item)
    signal indexChanged(int index)

    // ==================== Public Methods 公开方法 ====================
    function scrollToIndex(index) { core.scrollToIndex(index) }
    function scrollToTop() { core.scrollToTop() }
    function scrollToBottom() { core.scrollToBottom() }
    function smoothScrollTo(position) { core.smoothScrollTo(position) }
    function smoothScrollBy(delta) { core.smoothScrollBy(delta) }
    function itemAt(index) { return core.itemAt(index) }
    function indexAt(x, y) { return core.indexAt(x, y) }
    function syncNow() { core.syncNow() }

    // ==================== Content 内容 ====================
    // Default layout 默认布局
    ItemsStackLayout {
        id: defaultLayout
    }

    // Virtualizing host 虚拟化宿主
    ItemsRepeaterCore {
        id: core
        anchors.fill: parent
        host: control
        model: control.model
        delegate: control.delegate
        layout: control.activeLayout
        reuseItems: control.reuseItems
        cacheBuffer: control.cacheBuffer
        selectionController: control.selectionController
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
