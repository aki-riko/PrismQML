// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// HoverBehavior - Animated hover entry with immediate exit 悬浮进入动画与立即退出
Behavior {
    id: root

    required property bool active
    property bool animationEnabled: true
    property int enterDuration: Enums.duration.fast
    property int easingType: Easing.Linear
    property bool _initialized: false
    property bool _lastActive: false
    property bool _transitionWasActive: false
    property bool _awaitingActiveAfterTarget: false
    property bool _hasPendingActiveChange: false
    property bool _pendingFromActive: false
    property var _lastTargetValue: undefined
    property var _animationFrom: undefined
    property QtObject _unmatchedTargetTimer: Timer {
        interval: Enums.duration.none
        onTriggered: root._awaitingActiveAfterTarget = false
    }

    function _recordActiveChange() {
        if (!_initialized) {
            _lastActive = active
            return
        }
        if (_awaitingActiveAfterTarget) {
            _unmatchedTargetTimer.stop()
            _awaitingActiveAfterTarget = false
            _lastActive = active
            return
        }
        if (_hasPendingActiveChange) {
            // Two active flips without a target change cancel each other.
            // 目标未变化时连续两次 active 翻转应相互抵消。
            if (active === _pendingFromActive) {
                _hasPendingActiveChange = false
            }
        } else {
            _pendingFromActive = _lastActive
            _hasPendingActiveChange = true
        }
        _lastActive = active
    }

    function _selectTransitionDirection() {
        _prepareAnimationFrom()
        if (_hasPendingActiveChange) {
            _transitionWasActive = _pendingFromActive
            _hasPendingActiveChange = false
            _unmatchedTargetTimer.stop()
            _awaitingActiveAfterTarget = false
            return
        }
        _transitionWasActive = _lastActive
        _awaitingActiveAfterTarget = true
        _unmatchedTargetTimer.restart()
    }

    function _isColorValue(value) {
        return value !== undefined && value !== null
               && value.r !== undefined && value.g !== undefined
               && value.b !== undefined && value.a !== undefined
    }

    function _prepareAnimationFrom() {
        _animationFrom = undefined
        var previous = _lastTargetValue
        var next = targetValue
        if (_isColorValue(previous) && _isColorValue(next)
                && previous.a <= 0 && next.a > 0) {
            // Fade the intended hover color in from alpha zero instead of
            // interpolating RGB from transparent black. 从透明到悬浮色时只插值
            // alpha，避免透明黑参与 RGB 插值产生脏灰帧。
            _animationFrom = Qt.rgba(next.r, next.g, next.b, 0)
        }
        _lastTargetValue = next
    }

    enabled: animationEnabled
    Component.onCompleted: {
        _lastActive = active
        _lastTargetValue = targetValue
        _initialized = true
    }
    onAnimationEnabledChanged: {
        if (!animationEnabled) {
            _hasPendingActiveChange = false
            _awaitingActiveAfterTarget = false
            _unmatchedTargetTimer.stop()
            _lastActive = active
        }
    }
    onActiveChanged: _recordActiveChange()
    onTargetValueChanged: _selectTransitionDirection()

    PropertyAnimation {
        // Consume the state before this target change, independent of whether
        // active or the target binding was notified first. 使用目标变化前的状态，
        // 不依赖 active 与目标绑定的通知先后顺序。
        duration: root._transitionWasActive
                  ? Enums.motion.hoverExitDuration : root.enterDuration
        from: root._animationFrom
        easing.type: root.easingType
    }
}
