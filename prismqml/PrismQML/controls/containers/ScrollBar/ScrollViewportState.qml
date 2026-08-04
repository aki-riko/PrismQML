// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// ScrollViewportState - Stable scrollbar viewport state 稳定的滚动条视口状态
// Measures overflow without gutters first, then adds only cross-axis overflow.
// 先在无避让槽的完整视口中测量，再仅补充另一轴引起的溢出。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property Flickable target: null
    property bool scrollBarsEnabled: true
    property bool verticalEnabled: true
    property bool horizontalEnabled: false
    property bool alwaysShowVertical: false
    property bool alwaysShowHorizontal: false
    property int itemCount: -1

    // ==================== Internal Props 内部属性 ====================
    property bool _needsVertical: false
    property bool _needsHorizontal: false
    property bool _updatePending: false
    property bool _rerunRequested: false
    property bool _contentRerunRequested: false
    property bool _suppressViewportContentChanges: false
    property bool _completed: false
    property bool _destroying: false
    property bool _reserveVerticalGutter: false
    property bool _reserveHorizontalGutter: false
    property real _lastTargetWidth: -1
    property real _lastTargetHeight: -1
    property int _clearDeferrals: 0
    property int _phase: _phaseIdle
    property bool _baseVertical: false
    property bool _baseHorizontal: false

    // ==================== Readonly State 只读状态 ====================
    readonly property alias needsVertical: control._needsVertical
    readonly property alias needsHorizontal: control._needsHorizontal
    readonly property alias reserveVerticalGutter:
        control._reserveVerticalGutter
    readonly property alias reserveHorizontalGutter:
        control._reserveHorizontalGutter
    readonly property int _phaseIdle: 0
    readonly property int _phaseBegin: 1
    readonly property int _phaseMeasure: 2
    readonly property int _phaseSettle: 3
    readonly property int _phaseClear: 4
    readonly property int _phaseContentUpdate: 5
    readonly property int _phaseSuppressionClear: 6

    // ==================== Internal Methods 内部方法 ====================
    function _queuePhase(nextPhase) {
        if (_destroying) return
        _phase = nextPhase
        phaseTimer.restart()
    }

    function _queueContentUpdate() {
        if (_destroying) return
        _queuePhase(_phaseContentUpdate)
    }

    function _cancelDeferredPhase() {
        if (_phase !== _phaseContentUpdate
                && _phase !== _phaseSuppressionClear) return
        phaseTimer.stop()
        _phase = _phaseIdle
    }

    function _runPhase() {
        if (_destroying) return
        var currentPhase = _phase
        _phase = _phaseIdle
        switch (currentPhase) {
            case _phaseBegin:
                _beginMeasurement()
                break
            case _phaseMeasure:
                _measureWithoutGutters()
                break
            case _phaseSettle:
                _settleCrossAxis()
                break
            case _phaseClear:
                _clearPending()
                break
            case _phaseContentUpdate:
                scheduleUpdate()
                break
            case _phaseSuppressionClear:
                _clearPending()
                break
        }
    }

    function _clearPending() {
        if (_destroying) return
        if (_suppressViewportContentChanges && _clearDeferrals === 0) {
            // Virtual item views may defer relayout beyond one event-loop
            // turn. Keep their transaction open until content extents stay
            // quiet. 虚拟项视图的重排可能延后超过一轮事件循环；保持其
            // 事务到内容范围静默后再结束。
            _clearDeferrals = 1
            if (itemCount >= 0)
                _queuePhase(_phaseSuppressionClear)
            else
                _queuePhase(_phaseClear)
            return
        }
        if (target) {
            _lastTargetWidth = target.width
            _lastTargetHeight = target.height
        }
        _clearDeferrals = 0
        _suppressViewportContentChanges = false
        _updatePending = false
        if (_rerunRequested) {
            _rerunRequested = false
            _contentRerunRequested = false
            scheduleUpdate()
        } else if (_contentRerunRequested) {
            _contentRerunRequested = false
            _queueContentUpdate()
        }
    }

    function _handleContentChange() {
        if (_destroying || !target) return
        if (!_updatePending) {
            // Virtual views refine content extents while scrolling. Coalesce
            // those estimates so one scroll does not repeatedly remove and
            // restore gutters. 虚拟视图滚动时会持续修正内容范围；合并这些
            // 估算，避免一次滚动反复撤销并恢复 gutter。
            _queueContentUpdate()
            return
        }
        var viewportChanged = target.width !== _lastTargetWidth
            || target.height !== _lastTargetHeight
        _lastTargetWidth = target.width
        _lastTargetHeight = target.height
        if (viewportChanged) {
            // A viewport resize can emit both contentWidthChanged and
            // contentHeightChanged. Suppress the whole resulting relayout,
            // not only the first signal. 视口变尺可以连续触发内容宽高信号，
            // 必须把整轮重排作为同一次几何变化处理。
            _suppressViewportContentChanges = true
            _contentRerunRequested = false
        } else if (!_suppressViewportContentChanges) {
            _contentRerunRequested = true
        }
        if (_suppressViewportContentChanges && _clearDeferrals > 0
                && itemCount >= 0)
            _queuePhase(_phaseSuppressionClear)
    }

    function _settleCrossAxis() {
        if (_destroying) return
        if (!target) {
            _reserveVerticalGutter = false
            _reserveHorizontalGutter = false
            _needsVertical = false
            _needsHorizontal = false
            _updatePending = false
            return
        }
        var verticalEmpty = itemCount === 0 && !alwaysShowVertical
        var horizontalEmpty = itemCount === 0 && !alwaysShowHorizontal
        _needsVertical = !verticalEmpty && (_baseVertical
            || (scrollBarsEnabled && verticalEnabled
                && target.contentHeight > target.height))
        _needsHorizontal = !horizontalEmpty && (_baseHorizontal
            || (scrollBarsEnabled && horizontalEnabled
                && target.contentWidth > target.width))
        _reserveVerticalGutter = _needsVertical
        _reserveHorizontalGutter = _needsHorizontal
        // Keep geometry notifications suppressed until bindings and delegates settle.
        // 在绑定与委托完成布局前持续抑制由避让槽自身触发的几何通知。
        _queuePhase(_phaseClear)
    }

    function _measureWithoutGutters() {
        if (_destroying) return
        if (!target) {
            _reserveVerticalGutter = false
            _reserveHorizontalGutter = false
            _needsVertical = false
            _needsHorizontal = false
            _updatePending = false
            return
        }
        // ListView/GridView may retain the layout from the gutter-reduced width
        // for another turn. Commit that layout before reading content extents.
        // ListView/GridView 可能再保留一轮避让后宽度对应的布局；读取内容范围前先提交布局。
        if (typeof target.forceLayout === "function") target.forceLayout()
        var verticalEmpty = itemCount === 0 && !alwaysShowVertical
        var horizontalEmpty = itemCount === 0 && !alwaysShowHorizontal
        _baseVertical = !verticalEmpty && scrollBarsEnabled && verticalEnabled
            && (alwaysShowVertical || target.contentHeight > target.height)
        _baseHorizontal = !horizontalEmpty && scrollBarsEnabled && horizontalEnabled
            && (alwaysShowHorizontal || target.contentWidth > target.width)
        _lastTargetWidth = target.width
        _lastTargetHeight = target.height
        // Apply only the base gutters for cross-axis measurement. Keep the
        // committed visibility unchanged until the final state is known.
        // 仅为交叉轴测量应用基础 gutter，最终状态确定前不改变已提交可见性。
        _reserveVerticalGutter = _baseVertical
        _reserveHorizontalGutter = _baseHorizontal
        _queuePhase(_phaseSettle)
    }

    function _beginMeasurement() {
        if (_destroying) return
        if (!target || !scrollBarsEnabled) {
            _reserveVerticalGutter = false
            _reserveHorizontalGutter = false
            _needsVertical = false
            _needsHorizontal = false
            _updatePending = false
            _rerunRequested = false
            return
        }
        _lastTargetWidth = target.width
        _lastTargetHeight = target.height
        // Remove gutters without exposing the measurement phase as committed
        // scrollbar visibility. 仅撤销测量 gutter，不把测量中间态暴露为滚动条可见性。
        _reserveVerticalGutter = false
        _reserveHorizontalGutter = false
        _queuePhase(_phaseMeasure)
    }

    // ==================== Public Methods 公开方法 ====================
    function scheduleUpdate() {
        if (_destroying) return
        _cancelDeferredPhase()
        if (!target || !scrollBarsEnabled) {
            _reserveVerticalGutter = false
            _reserveHorizontalGutter = false
            _needsVertical = false
            _needsHorizontal = false
            _updatePending = false
            _rerunRequested = false
            return
        }
        if (_updatePending) return
        _updatePending = true
        _rerunRequested = false
        _contentRerunRequested = false
        _suppressViewportContentChanges = false
        _clearDeferrals = 0
        // Remove old gutters on the next turn so content signals cannot reenter layout.
        // 下一事件循环再撤销旧避让槽，避免内容信号重入布局。
        _queuePhase(_phaseBegin)
    }

    function invalidate() {
        if (_destroying || !_completed) return
        if (!target || !scrollBarsEnabled) {
            scheduleUpdate()
            return
        }
        if (_updatePending) {
            _rerunRequested = true
            return
        }
        scheduleUpdate()
    }

    width: 0
    height: 0
    visible: false

    onTargetChanged: invalidate()
    onScrollBarsEnabledChanged: invalidate()
    onVerticalEnabledChanged: invalidate()
    onHorizontalEnabledChanged: invalidate()
    onAlwaysShowVerticalChanged: invalidate()
    onAlwaysShowHorizontalChanged: invalidate()
    onItemCountChanged: invalidate()
    Component.onCompleted: {
        _completed = true
        invalidate()
    }
    Component.onDestruction: {
        _completed = false
        _destroying = true
        phaseTimer.stop()
        _phase = _phaseIdle
        _updatePending = false
        _rerunRequested = false
        _contentRerunRequested = false
        _suppressViewportContentChanges = false
        _reserveVerticalGutter = false
        _reserveHorizontalGutter = false
        _clearDeferrals = 0
    }

    // ==================== Content 内容 ====================
    Connections {
        function onContentHeightChanged() { control._handleContentChange() }
        function onContentWidthChanged() { control._handleContentChange() }

        target: control.target
        ignoreUnknownSignals: true
    }

    Timer {
        id: phaseTimer
        interval: control._phase === control._phaseContentUpdate
                  ? Enums.duration.fast
                  : (control._phase === control._phaseSuppressionClear
                     ? Enums.duration.instant : Enums.duration.none)
        repeat: false
        onTriggered: control._runPhase()
    }
}
