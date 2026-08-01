// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// DeterministicBounce - Time-bounded outward scroll phase and return 确定时限的滚动外移与回程
Item {
    id: control

    // ==================== Required Props 必需属性 ====================
    required property bool animated
    required property int sourceDuration
    required property int outwardDuration
    required property int returnDuration
    required property int easing
    required property real normalOutwardDistance
    required property real maxOutwardDistance
    required property real returnOvershoot

    // ==================== Public Props 公开属性 ====================
    property bool traceEnabled: false

    // ==================== Internal Props 内部属性 ====================
    property real _value: 0
    property real _startValue: 0
    property real _outwardValue: 0
    property real _returnValue: 0
    property bool _active: false
    property bool _outwardPhase: false
    property real _lastPublishedValue: 0
    property real _lastUpdateTimestamp: 0
    property real _adaptiveReturnOvershoot: 0
    property bool _retargeting: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool active: _active
    readonly property string phase: !_active ? "idle"
        : (_outwardPhase ? "outward" : "return")
    readonly property real _outwardProgress: sourceDuration > 0
        ? Math.min(1, outwardDuration / sourceDuration) : 1

    // ==================== Signals 信号 ====================
    signal positionChanged(real position)
    signal returnStarted()
    signal traceEvent(string stage, string details)

    // ==================== Public Methods 公开方法 ====================
    function start(startValue, outwardValue, returnValue) {
        stop("restart")
        _startValue = startValue
        _outwardValue = outwardValue
        _returnValue = returnValue
        _lastPublishedValue = startValue
        _lastUpdateTimestamp = Date.now()
        _adaptiveReturnOvershoot = _resolveReturnOvershoot()
        _outwardPhase = true
        _trace("start", "start=" + startValue +
               " outward=" + outwardValue +
               " return=" + returnValue +
               " adaptiveOvershoot=" + _adaptiveReturnOvershoot +
               " animated=" + animated)

        if (!animated) {
            _active = true
            _value = _outwardValue
            _trace("outward.immediate", "value=" + _value)
            immediateSequence.restart()
            return
        }

        outwardController.reload()
        outwardController.progress = 0
        _active = true
        _trace("outward.begin", "progress=" + outwardController.progress)
        outwardDriver.restart()
    }

    function extendOutward(outwardDelta) {
        if (!_active || !_outwardPhase) return false
        var previousValue = _value
        var previousStart = _startValue
        var previousOutward = _outwardValue
        var outwardDirection = previousOutward < _returnValue ? -1 : 1
        // Accumulate input only inside this outward phase and keep its fixed cap.
        // 只在本轮外移阶段累加输入，并继续遵守原有距离上限。
        var previousDistance = Math.abs(previousOutward - _returnValue)
        var nextDistance = Math.min(
            previousDistance + Math.max(0, outwardDelta), maxOutwardDistance)
        var outwardValue = _returnValue + outwardDirection * nextDistance
        if (!animated) {
            _outwardValue = outwardValue
            _adaptiveReturnOvershoot = _resolveReturnOvershoot()
            _value = outwardValue
            _trace("outward.extend", "progress=immediate" +
                   " previous=" + previousValue +
                   " value=" + _value +
                   " outward=" + outwardValue +
                   " delta=" + outwardDelta +
                   " adaptiveOvershoot=" + _adaptiveReturnOvershoot)
            return true
        }
        var progress = outwardController.progress
        var outwardSpan = previousOutward - previousStart
        var easedProgress = outwardSpan === 0
            ? 0 : (previousValue - previousStart) / outwardSpan
        var remainingProgress = 1 - easedProgress
        // Move the curve's effective start together with its endpoint so the
        // rendered position stays continuous while wall-clock progress is kept.
        // 终点更新时同步修正曲线有效起点，保持画面位置连续且不重启时间进度。
        _retargeting = true
        _startValue = remainingProgress === 0
            ? previousValue
            : (previousValue - easedProgress * outwardValue) / remainingProgress
        _outwardValue = outwardValue
        _adaptiveReturnOvershoot = _resolveReturnOvershoot()
        outwardController.reload()
        outwardController.progress = progress
        _retargeting = false
        _trace("outward.extend", "progress=" + progress +
               " previous=" + previousValue +
               " value=" + _value +
               " outward=" + outwardValue +
               " delta=" + outwardDelta +
               " adaptiveOvershoot=" + _adaptiveReturnOvershoot)
        return true
    }

    function stop(reason) {
        if (_active) {
            _trace("stop", "reason=" + (reason === undefined ? "requested" : reason) +
                   " phase=" + phase + " value=" + _value)
        }
        _active = false
        _outwardPhase = false
        outwardDriver.stop()
        returnAnimation.stop()
        immediateSequence.stop()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _trace(stage, details) {
        if (traceEnabled) traceEvent(stage, details)
    }

    function _startReturn(startValue, reason) {
        if (!_active || !_outwardPhase) return
        _outwardPhase = false
        outwardDriver.stop()
        var resolvedStart = startValue === undefined ? _value : startValue
        _trace("return.begin", "reason=" +
               (reason === undefined ? "requested" : reason) +
               " start=" + resolvedStart +
               " return=" + _returnValue +
               " adaptiveOvershoot=" + _adaptiveReturnOvershoot)
        returnStarted()
        if (!animated) {
            _value = _returnValue
            _finish()
            return
        }
        returnAnimation.from = resolvedStart
        returnAnimation.to = _returnValue
        returnAnimation.restart()
    }

    function _finish() {
        if (!_active) return
        _trace("finish", "value=" + _value + " return=" + _returnValue)
        _active = false
        _outwardPhase = false
    }

    function _resolveReturnOvershoot() {
        var normalDistance = Math.max(0, normalOutwardDistance)
        var maximumDistance = Math.max(normalDistance, maxOutwardDistance)
        var adaptiveSpan = maximumDistance - normalDistance
        var outwardDistance = Math.abs(_outwardValue - _returnValue)
        if (adaptiveSpan <= 0 || outwardDistance <= normalDistance) {
            return returnOvershoot
        }
        var distanceProgress = Math.min(
            1, (outwardDistance - normalDistance) / adaptiveSpan)
        return returnOvershoot * (1 - distanceProgress)
    }

    function _publishValue() {
        if (!_active || _retargeting) return
        var now = Date.now()
        // When one delayed frame consumes the complete outward window, the
        // animation driver catches up internally to the cutoff. Do not publish
        // that unseen peak; return from the last position actually rendered.
        // 单个延迟帧吞掉完整外移窗口时，驱动器会在内部补算到截止点；不要把这个
        // 未显示过的峰值再发布出去，直接从最后实际渲染的位置回程。
        if (_outwardPhase && _lastUpdateTimestamp > 0
                && now - _lastUpdateTimestamp >= outwardDuration) {
            _trace("outward.catchup-discard", "elapsed=" +
                   (now - _lastUpdateTimestamp) +
                   " discarded=" + _value +
                   " lastPublished=" + _lastPublishedValue)
            _startReturn(_lastPublishedValue, "delayed-frame")
            return
        }
        _lastUpdateTimestamp = now
        _lastPublishedValue = _value
        _trace(_outwardPhase ? "outward.frame" : "return.frame",
               "value=" + _value)
        positionChanged(_value)
    }

    width: 0
    height: 0
    visible: false

    on_ValueChanged: _publishValue()

    // Drive only the original first outwardDuration milliseconds of the source
    // easing curve. Normal frames may reach the cutoff; _publishValue discards
    // a catch-up frame after the complete outward window has already elapsed.
    // 只驱动原曲线最前面的 outwardDuration 毫秒；正常帧可到截止点，若完整外移窗口
    // 已在停顿中耗尽，_publishValue 会丢弃随后补算出的追赶帧。
    AnimationController {
        id: outwardController

        NumberAnimation {
            target: control
            property: "_value"
            from: control._startValue
            to: control._outwardValue
            duration: control.sourceDuration
            easing.type: control.easing
        }
    }

    NumberAnimation {
        id: outwardDriver
        target: outwardController
        property: "progress"
        from: 0
        to: control._outwardProgress
        duration: control.outwardDuration
        easing.type: Easing.Linear
        onFinished: control._startReturn(undefined, "outward-finished")
    }

    NumberAnimation {
        id: returnAnimation
        target: control
        property: "_value"
        duration: control.returnDuration
        easing.type: control.easing
        easing.overshoot: control._adaptiveReturnOvershoot
        onFinished: control._finish()
    }

    SequentialAnimation {
        id: immediateSequence

        PauseAnimation { duration: control.outwardDuration }
        ScriptAction { script: control._startReturn(undefined, "outward-timeout") }
    }
}
