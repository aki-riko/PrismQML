// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// SmoothScrollFrameDriver - Presented-frame synchronized smooth-scroll animation
// SmoothScrollFrameDriver - 跟随实际呈现帧的平滑滚动动画
Connections {
    id: frameDriver

    // ==================== Required Props 必需属性 ====================
    required property var scrollHelper
    required property bool verticalAxis

    // ==================== Internal Props 内部属性 ====================
    property real _fromValue: 0
    property real _toValue: 0
    property real _elapsedMilliseconds: 0
    property int _durationMilliseconds: 0
    property int _easingType: Easing.Linear
    property double _lastFrameTimestamp: 0
    property bool running: false

    // ==================== Public Methods 公开方法 ====================
    function moveTo(value) {
        var current = verticalAxis
            ? scrollHelper._smoothY : scrollHelper._smoothX
        var axisMatches = verticalAxis
            ? scrollHelper._isVertical : !scrollHelper._isVertical
        if (!scrollHelper.enabled || !axisMatches || scrollHelper._syncing
                || current === value) {
            setImmediate(value)
            return
        }
        _fromValue = current
        _toValue = value
        _elapsedMilliseconds = 0
        _durationMilliseconds = verticalAxis
            ? (scrollHelper._isOvershotV
                ? Enums.duration.bounce : scrollHelper.duration)
            : (scrollHelper._isOvershotH
                ? Enums.duration.bounce : scrollHelper.duration)
        _easingType = verticalAxis
            ? (scrollHelper._isOvershotV ? Easing.OutBack : scrollHelper.easing)
            : (scrollHelper._isOvershotH ? Easing.OutBack : scrollHelper.easing)
        if (_durationMilliseconds <= 0) {
            setImmediate(value)
            return
        }
        _lastFrameTimestamp = Date.now()
        running = true
        _requestNextFrame()
    }

    function setImmediate(value) {
        running = false
        scrollHelper._setSmoothPosition(verticalAxis, value)
        scrollHelper._onFrameDriverSettled(verticalAxis)
    }

    // ==================== Internal Methods 内部方法 ====================
    function _easedProgress(progress) {
        if (typeof WindowHelper !== "undefined" && WindowHelper
                && typeof WindowHelper.easingValueForProgress === "function") {
            return WindowHelper.easingValueForProgress(_easingType, progress)
        }
        var shifted = progress - 1
        if (_easingType === Easing.OutCubic) return shifted * shifted * shifted + 1
        if (_easingType === Easing.OutQuart) {
            return 1 - shifted * shifted * shifted * shifted
        }
        if (_easingType === Easing.OutBack) {
            var overshoot = 1.70158
            return shifted * shifted
                * ((overshoot + 1) * shifted + overshoot) + 1
        }
        return progress
    }

    function _advanceFrame(deltaMilliseconds) {
        _elapsedMilliseconds = Math.min(
            _durationMilliseconds,
            _elapsedMilliseconds + Math.max(0, deltaMilliseconds)
        )
        var progress = _elapsedMilliseconds / _durationMilliseconds
        var easedProgress = _easedProgress(progress)
        scrollHelper._setSmoothPosition(
            verticalAxis,
            _fromValue + (_toValue - _fromValue) * easedProgress
        )
        if (progress >= 1) {
            running = false
            scrollHelper._onFrameDriverSettled(verticalAxis)
        }
    }

    function _requestNextFrame() {
        if (running && target) target.update()
    }

    function onFrameSwapped() {
        var now = Date.now()
        _advanceFrame(now - _lastFrameTimestamp)
        _lastFrameTimestamp = now
        _requestNextFrame()
    }

    objectName: verticalAxis
        ? "smoothScrollVerticalFrameDriver"
        : "smoothScrollHorizontalFrameDriver"
    target: scrollHelper.target ? scrollHelper.target.Window.window : null
    enabled: running && target !== null
}
