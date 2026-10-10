// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../containers/ScrollBar"
import "RepeaterModel.js" as RepeaterModel

// ItemsRepeaterCore - Virtualizing delegate host 虚拟化委托宿主
// Owns the flickable viewport, the delegate recycle pool and the layout-driven
// arrangement. Only indices inside the layout's visible range hold a live delegate,
// so a huge model keeps a bounded number of objects.
// 持有可滑动视口、委托回收池与布局驱动的排布。只有布局可见范围内的索引持有存活委托,
// 因此超大模型也只保持有界的对象数量。
// Delegate contract 委托契约: declare `required property int index` and
// `required property var modelData`; the layout owns x/y/width/height.
// 委托契约: 必须声明 `required property int index` 与 `required property var modelData`;
// 位置与尺寸由布局接管。
Item {
    id: core

    // ==================== Required Props 必需属性 ====================
    // Owning entry; interaction policy and chrome colour are owned by the host.
    // 所属入口; 交互策略与底板颜色由宿主持有。
    required property var host

    // ==================== Public Props 公开属性 ====================
    property var model: []
    property Component delegate: null
    property var layout: null
    property bool reuseItems: true
    property int cacheBuffer: -1
    property int currentIndex: -1
    property var selectionController: null
    property bool showScrollBar: true
    property int scrollBarWidth: Enums.controlSize.scrollBarWidth
    property bool smoothScroll: true
    property bool dragScrollEnabled: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    property bool bounceEnabled: true

    // ==================== Internal Props 内部属性 ====================
    // Live delegates by index 按索引存放的存活委托
    property var _live: ({})
    // Recycled delegates 已回收委托
    property var _pool: []
    // Selection chrome by index 按索引存放的选择底板
    property var _chrome: ({})
    property var _chromePool: []
    property int _liveCount: 0
    property int _poolCount: 0
    property int _chromeCount: 0
    property bool _syncPending: false
    property bool _ready: false

    // ==================== Readonly State 只读状态 ====================
    readonly property int count: {
        var source = core.model
        if (source === null || source === undefined) return 0
        if (typeof source === "number") return Math.max(0, Math.floor(source))
        if (typeof source.count === "number") return Math.max(0, source.count)
        if (typeof source.length === "number") return Math.max(0, source.length)
        return 0
    }
    readonly property bool isVertical: core.layout === null
        || core.layout.scrollOrientation === Qt.Vertical
    readonly property bool _interactive: core.host !== null
        && core.host !== undefined && core.host.interactive === true
    readonly property color _chromeColor: core.host !== null
        && core.host !== undefined && core.host.selectionChromeColor !== undefined
        ? core.host.selectionChromeColor : Enums.stateColor.selected
    readonly property bool selectionChromeActive: core.selectionController !== null
        && core.selectionController.mode !== Enums.scroll.selection_none
    readonly property int instantiatedCount: core._liveCount
    readonly property int selectionChromeCount: core._chromeCount
    readonly property int recycledCount: core._poolCount
    // True once the viewport subtree exists; hosts gate object-valued wiring on it
    // because an alias to a not-yet-created object cannot be re-evaluated.
    // 视口子树就绪后为真; 宿主用它把对象型接线推迟, 因为指向尚未创建对象的别名无法重算。
    readonly property bool ready: core._ready
    readonly property alias flickableItem: flick
    readonly property alias contentX: flick.contentX
    readonly property alias contentY: flick.contentY
    readonly property alias contentWidth: flick.contentWidth
    readonly property alias contentHeight: flick.contentHeight
    readonly property alias _needsVertical: scrollViewportState.needsVertical
    readonly property alias _needsHorizontal: scrollViewportState.needsHorizontal
    readonly property real _scrollBarGutter:
        Math.max(0, core.scrollBarWidth) + Enums.spacing.xs

    // ==================== Signals 信号 ====================
    signal itemClicked(int index, var item)
    signal indexChanged(int index)

    // ==================== Public Methods 公开方法 ====================
    function scrollToIndex(index) {
        if (index < 0 || index >= core.count || core.layout === null) return
        var rect = core.layout.itemRect(index)
        if (!rect) return
        core.smoothScrollTo(core.isVertical
            ? Math.max(0, rect.y - (flick.height - rect.height) / 2)
            : Math.max(0, rect.x - (flick.width - rect.width) / 2))
    }

    function scrollToTop() { core._activeHelper().scrollToStart() }
    function scrollToBottom() { core._activeHelper().scrollToEnd() }
    function smoothScrollTo(position) { core._activeHelper().scrollTo(position) }
    function smoothScrollBy(delta) { core._activeHelper().scrollBy(delta) }
    function itemAt(index) { return core._live[index] }
    function indexAt(x, y) { return core.layout === null ? -1 : core.layout.indexAt(x, y) }
    // Force the pending visibility pass; tests and hosts may need it in one turn.
    // 立即执行待处理的可见性同步; 测试与宿主可能需要在同一轮内完成。
    function syncNow() { core._syncNow() }

    // ==================== Internal Methods 内部方法 ====================
    function _activeHelper() {
        return core.isVertical ? verticalHelper : horizontalHelper
    }

    function _requestSync() {
        if (core._syncPending) return
        core._syncPending = true
        syncTimer.restart()
    }

    function _syncNow() {
        core._syncPending = false
        if (core.layout === null || core.delegate === null) {
            core._releaseAll()
            core._syncChrome()
            return
        }
        var overscan = core._resolvedCacheBuffer()
        var offset = core.isVertical ? flick.contentY : flick.contentX
        var extent = core.isVertical ? flick.height : flick.width
        var range = core.layout.indexRangeFor(offset - overscan, extent + 2 * overscan)
        core._applyRange(
            Math.max(0, Math.min(range.first, core.count)),
            Math.min(core.count - 1, range.last))
        core._repositionLive()
        core._syncChrome()
    }

    function _resolvedCacheBuffer() {
        if (core.cacheBuffer >= 0) return core.cacheBuffer
        if (core.layout === null) return 0
        var rect = core.layout.itemRect(0)
        if (!rect) return 0
        return (core.isVertical ? rect.height : rect.width) * 2
    }

    function _applyRange(first, last) {
        var keys = Object.keys(core._live)
        for (var cursor = 0; cursor < keys.length; ++cursor) {
            var index = parseInt(keys[cursor], 10)
            if (index < first || index > last) core._releaseIndex(index)
        }
        for (var wanted = first; wanted <= last; ++wanted) {
            if (core._live[wanted] === undefined) core._acquireIndex(wanted)
        }
        core._updateCounts()
    }

    // JS array mutations are not notifiable, so the counters are republished here.
    // JS 数组的原地修改不会触发通知, 因此在这里重新发布计数。
    function _updateCounts() {
        core._liveCount = Object.keys(core._live).length
        core._poolCount = core._pool.length
    }

    function _repositionLive() {
        var keys = Object.keys(core._live)
        for (var cursor = 0; cursor < keys.length; ++cursor) {
            var index = parseInt(keys[cursor], 10)
            core._placeItem(core._live[index], index)
        }
    }

    function _acquireIndex(index) {
        if (core.delegate === null) return
        var item = core._pool.length > 0
            ? core._pool.pop()
            : core.delegate.createObject(flick.contentItem, {
                "index": index,
                "modelData": RepeaterModel.dataAt(core.model, index)
            })
        if (!item) return
        item.index = index
        item.modelData = RepeaterModel.dataAt(core.model, index)
        core._placeItem(item, index)
        item.visible = true
        core._live[index] = item
        if (core.selectionChromeActive) core._attachChrome(index)
    }

    function _placeItem(item, index) {
        if (!item || core.layout === null) return
        var rect = core.layout.itemRect(index)
        if (!rect) return
        item.x = rect.x
        item.y = rect.y
        item.width = rect.width
        item.height = rect.height
    }

    function _releaseIndex(index) {
        var item = core._live[index]
        delete core._live[index]
        core._detachChrome(index)
        if (!item) return
        if (core.reuseItems) {
            item.visible = false
            core._pool.push(item)
        } else {
            item.destroy()
        }
    }

    function _releaseAll() {
        var keys = Object.keys(core._live)
        for (var cursor = 0; cursor < keys.length; ++cursor) {
            core._releaseIndex(parseInt(keys[cursor], 10))
        }
        core._liveCount = 0
        core._chromeCount = 0
        core._updateCounts()
    }

    function _drainPool() {
        while (core._pool.length > 0) {
            var item = core._pool.pop()
            if (item) item.destroy()
        }
        core._poolCount = 0
    }

    function _drainChromePool() {
        while (core._chromePool.length > 0) {
            var chrome = core._chromePool.pop()
            if (chrome) chrome.destroy()
        }
    }

    function _attachChrome(index) {
        var chrome = core._chromePool.length > 0
            ? core._chromePool.pop()
            : chromeComponent.createObject(flick.contentItem)
        if (!chrome) return
        core._chrome[index] = chrome
        core._placeChrome(chrome, index)
        chrome.visible = true
    }

    function _placeChrome(chrome, index) {
        if (!chrome || core.layout === null) return
        var rect = core.layout.itemRect(index)
        if (!rect) return
        chrome.x = rect.x
        chrome.y = rect.y
        chrome.width = rect.width
        chrome.height = rect.height
    }

    function _detachChrome(index) {
        var chrome = core._chrome[index]
        delete core._chrome[index]
        if (!chrome) return
        if (core.reuseItems) {
            chrome.visible = false
            core._chromePool.push(chrome)
        } else {
            chrome.destroy()
        }
    }

    function _syncChrome() {
        if (!core.selectionChromeActive) {
            var stale = Object.keys(core._chrome)
            for (var staleCursor = 0; staleCursor < stale.length; ++staleCursor) {
                core._detachChrome(parseInt(stale[staleCursor], 10))
            }
            if (!core.reuseItems) core._drainChromePool()
            core._chromeCount = 0
            return
        }
        var existing = Object.keys(core._chrome)
        for (var cursor = 0; cursor < existing.length; ++cursor) {
            var index = parseInt(existing[cursor], 10)
            if (core._live[index] === undefined || !core._isSelected(index)) {
                core._detachChrome(index)
            } else {
                core._placeChrome(core._chrome[index], index)
            }
        }
        var liveKeys = Object.keys(core._live)
        for (var liveCursor = 0; liveCursor < liveKeys.length; ++liveCursor) {
            var liveIndex = parseInt(liveKeys[liveCursor], 10)
            if (core._isSelected(liveIndex) && core._chrome[liveIndex] === undefined) {
                core._attachChrome(liveIndex)
            }
        }
        core._chromeCount = Object.keys(core._chrome).length
    }

    function _isSelected(index) {
        return core.selectionController !== null
            && core.selectionController.isSelected(index)
    }

    function _refreshLiveData() {
        var keys = Object.keys(core._live)
        for (var cursor = 0; cursor < keys.length; ++cursor) {
            var index = parseInt(keys[cursor], 10)
            var item = core._live[index]
            if (item) item.modelData = RepeaterModel.dataAt(core.model, index)
        }
    }

    function _handleTap(index, modifiers) {
        if (index < 0) return
        core.currentIndex = index
        if (core.selectionController !== null) {
            core.selectionController.handleClick(index, modifiers)
        }
        core.itemClicked(index, RepeaterModel.dataAt(core.model, index))
    }

    onModelChanged: core._requestSync()
    onDelegateChanged: core._requestSync()
    onLayoutChanged: core._requestSync()
    onCountChanged: core._requestSync()
    onCacheBufferChanged: core._requestSync()
    onWidthChanged: core._requestSync()
    onHeightChanged: core._requestSync()
    onCurrentIndexChanged: core.indexChanged(core.currentIndex)
    onReuseItemsChanged: {
        if (!core.reuseItems) {
            core._drainPool()
            core._drainChromePool()
        }
    }
    onSelectionChromeActiveChanged: core._syncChrome()
    Component.onCompleted: {
        core._ready = true
        core._requestSync()
    }

    // ==================== Content 内容 ====================
    // Viewport 视口
    Flickable {
        id: flick
        anchors.fill: parent
        anchors.rightMargin: scrollViewportState.reserveVerticalGutter
            ? Math.min(core._scrollBarGutter, Math.max(0, core.width)) : 0
        anchors.bottomMargin: scrollViewportState.reserveHorizontalGutter
            ? Math.min(core._scrollBarGutter, Math.max(0, core.height)) : 0

        contentWidth: core.layout === null ? width : Math.max(core.layout.contentWidth, width)
        contentHeight: core.layout === null ? height : Math.max(core.layout.contentHeight, height)
        clip: true
        interactive: core.dragScrollEnabled
        boundsBehavior: core.bounceEnabled
            ? Flickable.DragAndOvershootBounds : Flickable.StopAtBounds

        onContentXChanged: core._requestSync()
        onContentYChanged: core._requestSync()
        onWidthChanged: core._requestSync()
        onHeightChanged: core._requestSync()

        // Tap layer. It is declared inside the viewport so the Flickable keeps its
        // drag-steal path; it exists only when the host asks for interaction.
        // 点击层声明在视口内部, 保持 Flickable 的拖拽抢占路径; 只有宿主启用交互时才存在。
        MouseArea {
            id: tapArea
            parent: flick.contentItem
            width: Math.max(flick.contentWidth, flick.width)
            height: Math.max(flick.contentHeight, flick.height)
            acceptedButtons: Qt.LeftButton
            enabled: core._interactive
            visible: core._interactive
            onClicked: function(mouse) {
                core._handleTap(core.indexAt(mouse.x, mouse.y), mouse.modifiers)
            }
        }
    }

    ScrollViewportState {
        id: scrollViewportState
        target: flick
        scrollBarsEnabled: core.showScrollBar
        verticalEnabled: core.isVertical
        horizontalEnabled: !core.isVertical
        itemCount: core.count
    }

    // Layout inputs. The repeater owns these three properties on the layout, so a
    // custom layout only has to declare them and compute its geometry from them.
    // 布局输入。重复器持有布局上的这三个属性, 自定义布局只需声明它们并据此计算几何。
    Binding {
        target: core.layout
        property: "viewportWidth"
        value: flick.width
        when: core.layout !== null
    }

    Binding {
        target: core.layout
        property: "viewportHeight"
        value: flick.height
        when: core.layout !== null
    }

    Binding {
        target: core.layout
        property: "count"
        value: core.count
        when: core.layout !== null
    }

    // Smooth scroll helpers 平滑滚动助手
    SmoothScrollHelper {
        id: verticalHelper
        target: flick
        orientation: Qt.Vertical
        enabled: core.smoothScroll && core.isVertical
        duration: core.scrollDuration
        step: core.scrollStep
        easing: core.scrollEasing
        bounceEnabled: core.bounceEnabled
        handleWheel: true
    }

    SmoothScrollHelper {
        id: horizontalHelper
        target: flick
        orientation: Qt.Horizontal
        enabled: core.smoothScroll && !core.isVertical
        duration: core.scrollDuration
        step: core.scrollStep
        easing: core.scrollEasing
        bounceEnabled: core.bounceEnabled
        handleWheel: true
    }

    // Scrollbars 滚动条
    ScrollBar {
        id: verticalBar
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: Enums.spacing.xxs
        target: flick
        scrollHelper: verticalHelper
        orientation: Qt.Vertical
        barWidth: Math.max(0, core.scrollBarWidth)
        visible: core.isVertical && core._needsVertical
    }

    ScrollBar {
        id: horizontalBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: Enums.spacing.xxs
        target: flick
        scrollHelper: horizontalHelper
        orientation: Qt.Horizontal
        barWidth: Math.max(0, core.scrollBarWidth)
        visible: !core.isVertical && core._needsHorizontal
    }

    // Deferred visibility pass 延迟可见性同步
    Timer {
        id: syncTimer
        interval: 0
        repeat: false
        onTriggered: core._syncNow()
    }

    // Live role updates 存活角色更新
    Connections {
        function onDataChanged() { core._refreshLiveData() }

        target: core.model !== null && core.model !== undefined
            && typeof core.model.dataChanged === "function" ? core.model : null
        ignoreUnknownSignals: true
    }

    // Selection state 选择状态
    Connections {
        function onSelectionChanged() { core._syncChrome() }

        target: core.selectionController
        ignoreUnknownSignals: true
    }

    // Selection chrome 选择底板
    Component {
        id: chromeComponent
        Rectangle {
            color: core._chromeColor
            radius: Enums.radius.small
            z: Enums.zIndex.background
        }
    }
}
