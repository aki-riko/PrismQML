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

    // ==================== Internal Props 内部属性 ====================
    property real _value: 0
    property real _startValue: 0
    property real _outwardValue: 0
    property real _returnValue: 0
    property bool _active: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool active: _active
    readonly property real _outwardProgress: sourceDuration > 0
        ? Math.min(1, outwardDuration / sourceDuration) : 1

    // ==================== Signals 信号 ====================
    signal positionChanged(real position)

    // ==================== Public Methods 公开方法 ====================
    function start(startValue, outwardValue, returnValue) {
        stop()
        _startValue = startValue
        _outwardValue = outwardValue
        _returnValue = returnValue

        if (!animated) {
            _active = true
            _value = _outwardValue
            immediateSequence.restart()
            return
        }

        outwardController.reload()
        outwardController.progress = 0
        _active = true
        outwardDriver.restart()
    }

    function stop() {
        _active = false
        outwardDriver.stop()
        returnAnimation.stop()
        immediateSequence.stop()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _startReturn() {
        if (!_active) return
        if (!animated) {
            _value = _returnValue
            _finish()
            return
        }
        returnAnimation.from = _value
        returnAnimation.to = _returnValue
        returnAnimation.restart()
    }

    function _finish() {
        if (!_active) return
        _active = false
    }

    width: 0
    height: 0
    visible: false

    on_ValueChanged: if (_active) positionChanged(_value)

    // Drive only the original first outwardDuration milliseconds of the
    // source easing curve. A delayed frame can reach this cutoff, never pass it.
    // 只驱动原曲线最前面的 outwardDuration 毫秒；延迟帧最多到截止点，不会继续外冲。
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
        onFinished: control._startReturn()
    }

    NumberAnimation {
        id: returnAnimation
        target: control
        property: "_value"
        duration: control.returnDuration
        easing.type: control.easing
        onFinished: control._finish()
    }

    SequentialAnimation {
        id: immediateSequence

        PauseAnimation { duration: control.outwardDuration }
        ScriptAction { script: control._startReturn() }
    }
}
