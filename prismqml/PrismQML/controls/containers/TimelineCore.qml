// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick as QtQ
import QtQuick.Effects
import "../.."
import "../icons"
import "../../effects"
import "Card"
import "../data/Label"
import "ScrollBar"
import "_internal" as TimelineInternal

// TimelineCore - Timeline widget 时间线组件
// Supports grouped items with status icons and cards 支持分组项目、状态图标和卡片
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Items format: [{title: "已完成", status: "success", cards: [{text: "Task1", status: "success", strikeOut: true}]}, ...]
    // status: "success", "info", "warning", "error"
    property var items: []

    // Visual type: standard grouped timeline or generic graph timeline.
    // Graph cards may provide graph:{nodeLane,nodeColorIndex,segments:[{fromLane,toLane,colorIndex}]}
    // and labels:[{text,status}]. Group graph data draws lanes through date headers.
    property int type: Enums.timeline.type_standard
    property int graphLaneCount: 1
    property var graphPalette: Enums.chartColors.extendedPalette

    // 虚拟滚动:默认关(保持原 Column+Repeater 全量渲染,向后兼容)。
    // 开启后整个组件改用单层 ListView 渲染,把 items 拍平成行(组头行+卡片行),
    // 只渲染可见项,适合大列表(上千条)。开启时组件自身可滚动,需给定 height。
    // Virtual scrolling: off by default (keeps original full render, backward compatible).
    property bool virtualized: false
    property bool showScrollBar: true
    property int scrollBarWidth: Enums.controlSize.scrollBarWidth

    // 选中项的 key 值(配合 selectedRole 高亮当前选中卡片);为空不高亮
    property string selectedRole: "commit"   // card 对象里用作唯一标识的字段名
    property var selectedKey: undefined        // 当前选中值(与 card[selectedRole] 比对)

    // ==================== Internal Props 内部属性 ====================
    property var _flatRows: []
    property var _flatGroupSignatures: []
    property string _flatLastGroupHeaderSignature: ""
    property var _flatLastCardSignatures: []
    property int _flatGroupCount: 0
    property int _lastFlatBuildGroupCount: 0
    property real _pulsePhase: Enums.opacityLevel.invisible

    // ==================== Readonly State 只读状态 ====================
    readonly property var _safeItems:
        items === null || items === undefined ? []
        : (typeof items.length === "number" ? items : [])
    readonly property bool _graphMode: type === Enums.timeline.type_graph
    readonly property bool _usesVirtualList: virtualized || _graphMode
    readonly property alias _needsVirtualScrollBar: scrollViewportState.needsVertical
    readonly property alias _reserveVirtualScrollBarGutter:
        scrollViewportState.reserveVerticalGutter
    readonly property real _visualOvershootOffset: vScrollHelper._visualOvershootOffset
    readonly property real _scrollBarGutter:
        Math.max(0, scrollBarWidth) + Enums.spacing.xs
    readonly property real _graphWidth: Enums.spacing.timelineGraphPadding * 2
        + Math.max(1, graphLaneCount) * Enums.spacing.timelineGraphLane
    readonly property real _pulseOpacity: Enums.opacityLevel.strong
        + (Enums.opacityLevel.visible - Enums.opacityLevel.strong)
            * (Enums.opacityLevel.visible - _pulsePhase)
    // ==================== Signals 信号 ====================
    signal itemClicked(int groupIndex, string title)
    signal cardClicked(int groupIndex, int cardIndex, string text)
    // cardClickedData: 回传完整 card 对象(含调用方自定义字段,如业务 id/hash)
    // cardClickedData: emits the full card object (carrying caller's custom fields, e.g. business id/hash)
    signal cardClickedData(int groupIndex, int cardIndex, var cardData)
    // 虚拟滚动模式下滚动到接近底部时触发(用于分页加载更多)
    signal reachedEnd()

    // ==================== Internal Methods 内部方法 ====================
    function _rowsForGroup(group, groupIndex) {
        var grp = group || {}
        var rows = []
        var groupStatus = grp.status || "info"
        rows.push({
            "kind": "header", "groupIndex": groupIndex,
            "title": grp.title || "", "dateKey": grp.dateKey || "",
            "status": groupStatus,
            "graphData": grp.graph || {}
        })
        var cards = grp.cards || []
        for (var cardIndex = 0; cardIndex < cards.length; cardIndex++) {
            var card = cards[cardIndex]
            var cardObject = card && typeof card === "object"
            rows.push({
                "kind": "card", "groupIndex": groupIndex, "cardIndex": cardIndex,
                "groupStatus": groupStatus, "cardData": card,
                "text": typeof card === "string" ? card : (cardObject ? card.text || "" : ""),
                "description": cardObject ? card.description || "" : "",
                "time": cardObject ? card.time || "" : "",
                "timePeriod": cardObject ? card.timePeriod || "" : "",
                "status": cardObject ? card.status || groupStatus : groupStatus,
                "strikeOut": cardObject ? card.strikeOut || false : false,
                "graphData": cardObject ? card.graph || {} : {},
                "isLastCard": cardIndex === cards.length - 1
            })
        }
        return rows
    }

    function _clearFlatState() {
        _flatModel.clear()
        _flatRows = []
        _flatGroupSignatures = []
        _flatLastGroupHeaderSignature = ""
        _flatLastCardSignatures = []
        _flatGroupCount = 0
        _lastFlatBuildGroupCount = 0
    }

    function _groupSignatures(source) {
        var signatures = []
        for (var index = 0; index < source.length; index++) {
            signatures.push(JSON.stringify(source[index]))
        }
        return signatures
    }

    function _groupHeaderSignature(group) {
        var grp = group || {}
        return JSON.stringify({
            "title": grp.title || "",
            "status": grp.status || "info",
            "dateKey": grp.dateKey || "",
            "graphData": grp.graph || {}
        })
    }

    function _cardSignatures(group) {
        var cards = (group || {}).cards || []
        var signatures = []
        for (var index = 0; index < cards.length; index++) {
            signatures.push(JSON.stringify(cards[index]))
        }
        return signatures
    }

    function _commonPrefixGroupCount(signatures) {
        var limit = Math.min(_flatGroupCount, signatures.length)
        var count = 0
        while (count < limit
                && signatures[count] === _flatGroupSignatures[count]) count++
        return count
    }

    function _isSignaturePrefix(previous, current) {
        if (current.length <= previous.length) return false
        for (var index = 0; index < previous.length; index++) {
            if (previous[index] !== current[index]) return false
        }
        return true
    }

    function _tailAppendSignatures(source, prefixGroupCount) {
        if (_flatGroupCount <= 0 || source.length < _flatGroupCount) return []
        var tailGroupIndex = _flatGroupCount - 1
        if (prefixGroupCount !== tailGroupIndex) return []
        if (_groupHeaderSignature(source[tailGroupIndex])
                !== _flatLastGroupHeaderSignature) return []
        var signatures = _cardSignatures(source[tailGroupIndex])
        return _isSignaturePrefix(_flatLastCardSignatures, signatures)
            ? signatures : []
    }

    function _rowStartIndexForGroup(groupIndex) {
        if (groupIndex <= 0) return 0
        for (var rowIndex = 0; rowIndex < _flatRows.length; rowIndex++) {
            if (_flatRows[rowIndex].groupIndex >= groupIndex) return rowIndex
        }
        return _flatRows.length
    }

    function _appendRows(rows, startIndex, nextRows) {
        for (var rowIndex = startIndex; rowIndex < rows.length; rowIndex++) {
            nextRows.push(rows[rowIndex])
            _flatModel.append(rows[rowIndex])
        }
    }

    function _appendGroups(source, startGroupIndex, nextRows) {
        for (var groupIndex = startGroupIndex;
                groupIndex < source.length; groupIndex++) {
            _appendRows(_rowsForGroup(source[groupIndex], groupIndex), 0, nextRows)
        }
    }

    function _replaceFlatSuffix(source, startGroupIndex) {
        var rowStartIndex = _rowStartIndexForGroup(startGroupIndex)
        var removeCount = _flatModel.count - rowStartIndex
        if (removeCount > 0) _flatModel.remove(rowStartIndex, removeCount)
        var nextRows = _flatRows.slice(0, rowStartIndex)
        _appendGroups(source, startGroupIndex, nextRows)
        _flatRows = nextRows
        _lastFlatBuildGroupCount = source.length - startGroupIndex
    }

    function _appendTailGrowth(source) {
        var tailGroupIndex = _flatGroupCount - 1
        var previousCardCount = _flatLastCardSignatures.length
        var tailRows = _rowsForGroup(source[tailGroupIndex], tailGroupIndex)
        var nextRows = _flatRows.slice()
        if (previousCardCount > 0) {
            var lastCardRowIndex = _rowStartIndexForGroup(tailGroupIndex)
                + previousCardCount
            nextRows[lastCardRowIndex].isLastCard = false
            _flatModel.setProperty(lastCardRowIndex, "isLastCard", false)
        }
        _appendRows(tailRows, previousCardCount + 1, nextRows)
        _appendGroups(source, _flatGroupCount, nextRows)
        _flatRows = nextRows
        _lastFlatBuildGroupCount = source.length - tailGroupIndex
    }

    function _rememberFlatSource(source, signatures) {
        _flatGroupSignatures = signatures
        _flatGroupCount = source.length
        if (source.length === 0) {
            _flatLastGroupHeaderSignature = ""
            _flatLastCardSignatures = []
            return
        }
        var lastGroup = source[source.length - 1]
        _flatLastGroupHeaderSignature = _groupHeaderSignature(lastGroup)
        _flatLastCardSignatures = _cardSignatures(lastGroup)
    }

    function _syncFlat() {
        if (!_usesVirtualList) {
            _clearFlatState()
            return
        }
        var source = _safeItems || []
        var signatures = _groupSignatures(source)
        var prefixGroupCount = _commonPrefixGroupCount(signatures)
        if (prefixGroupCount === source.length
                && source.length === _flatGroupCount) {
            _rememberFlatSource(source, signatures)
            return
        }
        var tailSignatures = _tailAppendSignatures(source, prefixGroupCount)
        if (tailSignatures.length > 0)
            _appendTailGrowth(source)
        else
            _replaceFlatSuffix(source, prefixGroupCount)
        _rememberFlatSource(source, signatures)
    }

    function _scheduleScrollBarUpdate() {
        if (scrollViewportState) scrollViewportState.invalidate()
    }

    function _getStatusColor(status) {
        switch (status) {
            case "success": return Enums.statusLevel.getColor("success")
            case "warning": return Enums.statusLevel.getColor("warning")
            case "error": return Enums.statusLevel.getColor("error")
            default: return Enums.accentColor  // info
        }
    }

    function _getTimeColor(period) {
        if (period === "AM") return Enums.accentColor
        if (period === "PM") return Enums.statusLevel.getColor("warning")
        return Enums.accentColor
    }

    function _getStatusIcon(status) {
        switch (status) {
            case "success": return "Checkmark"      // 简单勾号，不带圆圈
            case "warning": return "Warning"        // 感叹号三角
            case "error": return "Dismiss"          // 简单X，不带圆圈
            default: return "Info"                  // info - i图标
        }
    }

    on_UsesVirtualListChanged: _syncFlat()
    on_SafeItemsChanged: _syncFlat()
    onShowScrollBarChanged: _scheduleScrollBarUpdate()
    onScrollBarWidthChanged: _scheduleScrollBarUpdate()
    onWidthChanged: _scheduleScrollBarUpdate()
    onHeightChanged: _scheduleScrollBarUpdate()
    Component.onCompleted: {
        _syncFlat()
        _scheduleScrollBarUpdate()
    }

    implicitWidth: 400
    implicitHeight: _usesVirtualList ? 400 : contentColumn.implicitHeight

    // One shared breathing driver keeps every visible timeline row in phase.
    // 单个共享呼吸驱动让所有可见时间线行保持同相，避免逐节点循环动画。
    SequentialAnimation on _pulsePhase {
        running: control.visible && control.enabled
        loops: Animation.Infinite
        NumberAnimation {
            to: Enums.opacityLevel.strong
            duration: Enums.duration.xslow
            easing.type: Easing.InOutSine
        }
        NumberAnimation {
            to: Enums.opacityLevel.visible
            duration: Enums.duration.xslow
            easing.type: Easing.InOutSine
        }
    }

    // ==================== Content 内容 ====================
    // 虚拟模式实际驱动 ListView 的 ListModel(增量同步,避免整体替换导致滚动跳顶)
    QtQ.ListModel { id: _flatModel }

    // Non-virtual content: full Column and Repeater 非虚拟内容：全量 Column 与 Repeater
    TimelineInternal.TimelineStandardContent {
        id: contentColumn
        timeline: control
    }

    // Virtual content: flattened ListView renders visible rows 虚拟内容：拍平 ListView 仅渲染可见行
    QtQ.ListView {
        id: virtualList
        property var timelineControl: control
        objectName: "timelineVirtualViewport"
        anchors.fill: parent
        anchors.rightMargin: control._reserveVirtualScrollBarGutter
            ? Math.min(control._scrollBarGutter, Math.max(0, parent.width)) : 0
        visible: control._usesVirtualList
        model: control._usesVirtualList ? _flatModel : null
        clip: true
        cacheBuffer: 600
        reuseItems: true   // 复用 delegate,滚动时不重复实例化(大列表性能关键)
        interactive: false // 关原生 flick,交给 SmoothScrollHelper 接管(否则平滑滚动不生效)
        boundsBehavior: Flickable.DragAndOvershootBounds
        onContentYChanged: {
            if (contentHeight > height && contentY + height >= contentHeight - 600)
                control.reachedEnd()
        }

        delegate: TimelineInternal.TimelineVirtualRow {}

        // 平滑滚动(滚轮缓动,与其他 Fluent 列表一致)
        SmoothScrollHelper {
            id: vScrollHelper
            target: virtualList
            orientation: Qt.Vertical
            handleWheel: true
            bounceEnabled: true
            _visualOvershootEnabled: true
        }

    }

    ScrollViewportState {
        id: scrollViewportState
        target: virtualList
        scrollBarsEnabled: control._usesVirtualList && control.showScrollBar
        verticalEnabled: true
        itemCount: virtualList.count
    }

    // Fluent scrollbar stays outside the reduced virtual viewport.
    // Fluent 滚动条位于缩小后的虚拟视口之外。
    ScrollBar {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: Enums.spacing.xxs
        target: virtualList
        scrollHelper: vScrollHelper
        barWidth: Math.max(0, control.scrollBarWidth)
        visible: control._needsVirtualScrollBar
    }
}
