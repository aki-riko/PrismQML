// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

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
    property bool _destroying: false
    property real _lastTargetWidth: -1
    property real _lastTargetHeight: -1
    property int _phase: _phaseIdle
    property bool _baseVertical: false
    property bool _baseHorizontal: false

    // ==================== Readonly State 只读状态 ====================
    readonly property alias needsVertical: control._needsVertical
    readonly property alias needsHorizontal: control._needsHorizontal
    readonly property int _phaseIdle: 0
    readonly property int _phaseBegin: 1
    readonly property int _phaseMeasure: 2
    readonly property int _phaseSettle: 3
    readonly property int _phaseClear: 4

    // ==================== Internal Methods 内部方法 ====================
    function _queuePhase(nextPhase) {
        if (_destroying) return
        _phase = nextPhase
        phaseTimer.restart()
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
        }
    }

    function _clearPending() {
        if (_destroying) return
        if (target) {
            _lastTargetWidth = target.width
            _lastTargetHeight = target.height
        }
        _updatePending = false
        if (_rerunRequested) {
            _rerunRequested = false
            scheduleUpdate()
        }
    }

    function _handleContentChange() {
        if (_destroying || !target) return
        if (!_updatePending) {
            scheduleUpdate()
            return
        }
        var viewportChanged = target.width !== _lastTargetWidth
            || target.height !== _lastTargetHeight
        _lastTargetWidth = target.width
        _lastTargetHeight = target.height
        if (!viewportChanged) _rerunRequested = true
    }

    function _settleCrossAxis() {
        if (_destroying) return
        if (!target) {
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
        // Keep geometry notifications suppressed until bindings and delegates settle.
        // 在绑定与委托完成布局前持续抑制由避让槽自身触发的几何通知。
        _queuePhase(_phaseClear)
    }

    function _measureWithoutGutters() {
        if (_destroying) return
        if (!target) {
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
        _needsVertical = _baseVertical
        _needsHorizontal = _baseHorizontal
        _queuePhase(_phaseSettle)
    }

    function _beginMeasurement() {
        if (_destroying) return
        if (!target || !scrollBarsEnabled) {
            _needsVertical = false
            _needsHorizontal = false
            _updatePending = false
            _rerunRequested = false
            return
        }
        _lastTargetWidth = target.width
        _lastTargetHeight = target.height
        // Change viewport geometry outside target geometry-change signal delivery.
        // 在目标几何变化信号派发结束后再改变视口，避免重入布局绑定。
        _needsVertical = false
        _needsHorizontal = false
        _queuePhase(_phaseMeasure)
    }

    // ==================== Public Methods 公开方法 ====================
    function scheduleUpdate() {
        if (_destroying) return
        if (!target || !scrollBarsEnabled) {
            _needsVertical = false
            _needsHorizontal = false
            _updatePending = false
            _rerunRequested = false
            return
        }
        if (_updatePending) return
        _updatePending = true
        _rerunRequested = false
        // Remove old gutters on the next turn so content signals cannot reenter layout.
        // 下一事件循环再撤销旧避让槽，避免内容信号重入布局。
        _queuePhase(_phaseBegin)
    }

    function invalidate() {
        if (_destroying) return
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
    Component.onCompleted: invalidate()
    Component.onDestruction: {
        _destroying = true
        phaseTimer.stop()
        _phase = _phaseIdle
        _updatePending = false
        _rerunRequested = false
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
        interval: 0
        repeat: false
        onTriggered: control._runPhase()
    }
}
