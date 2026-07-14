// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "ChartViewportTransition.js" as ViewportTransition

// ChartViewportAnimator - One-shot viewport data and transform animator 一次性视窗数据与变换动画器
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property real viewportStart: 0
    property real viewportEnd: 1
    property bool animated: true
    property bool interactive: false
    property bool transitionEnabled: true

    // ==================== Readonly State 只读状态 ====================
    readonly property var renderViewport: _renderViewport
    readonly property real renderStart: _renderViewport.start
    readonly property real renderEnd: _renderViewport.end
    readonly property var visualViewport: ViewportTransition.visualRange(
        renderStart, renderEnd, scaleValue, offsetRatio
    )
    readonly property real visualStart: visualViewport.start
    readonly property real visualEnd: visualViewport.end
    readonly property bool active: viewportAnimation.running

    // ==================== Internal Props 内部属性 ====================
    property var _renderViewport: ({ start: viewportStart, end: viewportEnd })
    property real scaleValue: 1
    property real offsetRatio: 0
    property real _scaleTo: 1
    property real _offsetTo: 0
    property var _commitTarget: null
    property bool _transitionPending: false
    property bool _ready: false

    // ==================== Signals 信号 ====================
    signal transitionStarted()
    signal transitionFinished()

    // ==================== Internal Methods 内部方法 ====================
    function _scheduleTransition() {
        if (!_ready || _transitionPending) return
        _transitionPending = true
        Qt.callLater(control._applyTransition)
    }

    function _snapToTarget() {
        viewportAnimation.stop()
        _transitionPending = false
        _commitTarget = null
        _renderViewport = { start: viewportStart, end: viewportEnd }
        scaleValue = 1
        offsetRatio = 0
    }

    function _applyTransition() {
        _transitionPending = false
        if (!_ready) return
        var transitionPlan = ViewportTransition.plan(
            renderStart, renderEnd, scaleValue, offsetRatio,
            viewportStart, viewportEnd, Enums.chart.viewport_epsilon
        )
        viewportAnimation.stop()
        transitionStarted()
        if (!animated || interactive || !transitionEnabled || !transitionPlan.animate) {
            _snapToTarget()
            return
        }
        if (transitionPlan.replaceData) {
            _renderViewport = { start: viewportStart, end: viewportEnd }
        }
        scaleValue = transitionPlan.scaleFrom
        offsetRatio = transitionPlan.offsetFrom
        _scaleTo = transitionPlan.scaleTo
        _offsetTo = transitionPlan.offsetTo
        _commitTarget = transitionPlan.commitAfter
            ? { start: viewportStart, end: viewportEnd }
            : null
        viewportAnimation.restart()
    }

    function _completeTransition() {
        if (_commitTarget) {
            _renderViewport = {
                start: _commitTarget.start,
                end: _commitTarget.end
            }
        }
        _commitTarget = null
        scaleValue = 1
        offsetRatio = 0
        transitionFinished()
    }

    width: 0
    height: 0

    onViewportStartChanged: _scheduleTransition()
    onViewportEndChanged: _scheduleTransition()
    onAnimatedChanged: if (_ready && !animated) _snapToTarget()
    onTransitionEnabledChanged: if (_ready && !transitionEnabled) _snapToTarget()
    Component.onCompleted: {
        _ready = true
        _snapToTarget()
    }

    ParallelAnimation {
        id: viewportAnimation

        onFinished: control._completeTransition()

        NumberAnimation {
            target: control
            property: "scaleValue"
            to: control._scaleTo
            duration: Enums.duration.normal
            easing.type: Easing.OutCubic
        }
        NumberAnimation {
            target: control
            property: "offsetRatio"
            to: control._offsetTo
            duration: Enums.duration.normal
            easing.type: Easing.OutCubic
        }
    }
}
