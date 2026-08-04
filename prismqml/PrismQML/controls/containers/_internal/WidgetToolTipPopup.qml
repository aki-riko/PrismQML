// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "../../.."

// WidgetToolTipPopup - Window-backed tooltip popup Widget 窗口工具提示弹层
Popup {
    id: toolTip

    // ==================== Required Props 必需属性 ====================
    required property var widget

    // ==================== Internal Props 内部属性 ====================
    property bool _pendingShow: false
    property QtObject _showTimer: null
    property QtObject _hideTimer: null
    property QtObject _autoHideTimer: null
    readonly property int _tooltipTextWidth: Math.min(
        Math.ceil(_tooltipMetrics.advanceWidth),
        Enums.controlSize.tooltipMaxWidth)

    // ==================== Internal Methods 内部方法 ====================
    function _screenBounds(sourcePos) {
        var screenGeometry = WindowHelper.availableScreenGeometryAt(
            Math.round(sourcePos.x + widget.width / 2),
            Math.round(sourcePos.y + widget.height / 2))
        if (screenGeometry && screenGeometry.width > 0 && screenGeometry.height > 0) {
            return {
                left: screenGeometry.x,
                top: screenGeometry.y,
                right: screenGeometry.x + screenGeometry.width,
                bottom: screenGeometry.y + screenGeometry.height
            }
        }
        return {
            left: widget.Screen.virtualX,
            top: widget.Screen.virtualY,
            right: widget.Screen.virtualX + widget.Screen.width,
            bottom: widget.Screen.virtualY + widget.Screen.height
        }
    }
    function _directionOrder() {
        if (widget.toolTipPosition === Enums.position.right)
            return [Enums.position.right, Enums.position.left,
                    Enums.position.top, Enums.position.bottom]
        if (widget.toolTipPosition === Enums.position.left)
            return [Enums.position.left, Enums.position.right,
                    Enums.position.top, Enums.position.bottom]
        if (widget.toolTipPosition === Enums.position.bottom)
            return [Enums.position.bottom, Enums.position.top,
                    Enums.position.right, Enums.position.left]
        return [Enums.position.top, Enums.position.bottom,
                Enums.position.right, Enums.position.left]
    }
    function _directionFits(direction, sourcePos, bounds) {
        var gap = Enums.spacing.xs
        if (direction === Enums.position.right)
            return sourcePos.x + widget.width + gap + toolTip.width <= bounds.right
        if (direction === Enums.position.left)
            return sourcePos.x - gap - toolTip.width >= bounds.left
        if (direction === Enums.position.bottom)
            return sourcePos.y + widget.height + gap + toolTip.height <= bounds.bottom
        return sourcePos.y - gap - toolTip.height >= bounds.top
    }
    function _resolvedDirection(sourcePos, bounds) {
        var order = _directionOrder()
        for (var i = 0; i < order.length; i++) {
            if (_directionFits(order[i], sourcePos, bounds)) return order[i]
        }
        return order[0]
    }
    function _clamp(value, minimum, maximum) {
        return Math.max(minimum, Math.min(value, maximum))
    }
    function _applyPosition(direction, sourcePos, bounds) {
        var gap = Enums.spacing.xs
        if (direction === Enums.position.right || direction === Enums.position.left) {
            x = direction === Enums.position.right
                ? widget.width + gap : -toolTip.width - gap
            var globalY = sourcePos.y + (widget.height - toolTip.height) / 2
            y = _clamp(globalY, bounds.top,
                       Math.max(bounds.top, bounds.bottom - toolTip.height)) - sourcePos.y
            return
        }
        y = direction === Enums.position.bottom
            ? widget.height + gap : -toolTip.height - gap
        var globalX = sourcePos.x + (widget.width - toolTip.width) / 2
        x = _clamp(globalX, bounds.left,
                   Math.max(bounds.left, bounds.right - toolTip.width)) - sourcePos.x
    }
    function _updatePosition() {
        var sourcePos = widget.mapToGlobal(0, 0)
        var bounds = _screenBounds(sourcePos)
        _applyPosition(_resolvedDirection(sourcePos, bounds), sourcePos, bounds)
    }
    function _createLifecycleTimer(timerInterval, triggerCallback, releaseCallback) {
        var timer = lifecycleTimerComponent.createObject(
            toolTip.contentItem,
            {
                "timerInterval": timerInterval,
                "triggerCallback": triggerCallback,
                "releaseCallback": releaseCallback
            }
        )
        if (!timer) console.error("Widget tooltip failed to create lifecycle timer")
        return timer
    }
    function _disposeTimer(timer) {
        if (!timer) return
        timer.stop()
        timer.destroy()
    }
    function _cancelShowTimer() {
        var timer = _showTimer
        _showTimer = null
        _disposeTimer(timer)
    }
    function _cancelHideTimer() {
        var timer = _hideTimer
        _hideTimer = null
        _disposeTimer(timer)
    }
    function _cancelAutoHideTimer() {
        var timer = _autoHideTimer
        _autoHideTimer = null
        _disposeTimer(timer)
    }
    function _startAutoHideTimer() {
        if (!_autoHideTimer) {
            _autoHideTimer = _createLifecycleTimer(
                widget.toolTipDuration,
                function() { toolTip.hide() },
                function(timer) {
                    if (toolTip._autoHideTimer === timer)
                        toolTip._autoHideTimer = null
                }
            )
        }
        if (_autoHideTimer) {
            _autoHideTimer.timerInterval = widget.toolTipDuration
            _autoHideTimer.start()
        }
    }
    function show() {
        widget._toolTipShowPending = false
        _pendingShow = true
        _updatePosition()
        Qt.callLater(_doOpen)
    }
    function hide() {
        widget._toolTipShowPending = false
        _pendingShow = false
        toolTip.close()
    }
    function dismiss() {
        widget._toolTipShowPending = false
        _pendingShow = false
        // Explicit dismissal must not overlap a menu with the exit animation.
        // 显式隐藏不能让退出动画继续与菜单重叠显示。
        var enterTransition = toolTip.enter
        var exitTransition = toolTip.exit
        toolTip.enter = null
        toolTip.exit = null
        if (toolTip.visible) {
            toolTip.open()
            toolTip.close()
        }
        toolTip.enter = enterTransition
        toolTip.exit = exitTransition
    }
    function startShowTimer(elapsedMilliseconds) {
        var remainingDelay = Math.max(
            0, widget.toolTipShowDelay - elapsedMilliseconds)
        if (!_showTimer) {
            _showTimer = _createLifecycleTimer(
                remainingDelay,
                function() {
                    toolTip.show()
                    if (toolTip.widget.toolTipDuration > 0)
                        toolTip._startAutoHideTimer()
                },
                function(timer) {
                    if (toolTip._showTimer === timer) toolTip._showTimer = null
                }
            )
        }
        if (_showTimer) {
            _showTimer.timerInterval = remainingDelay
            _showTimer.restart()
        }
    }
    function stopShowTimer() {
        _cancelShowTimer()
    }
    function startHideTimer() {
        if (!_hideTimer) {
            _hideTimer = _createLifecycleTimer(
                widget.toolTipHideDelay,
                function() { toolTip.hide() },
                function(timer) {
                    if (toolTip._hideTimer === timer) toolTip._hideTimer = null
                }
            )
        }
        if (_hideTimer) _hideTimer.start()
    }
    function cancelTimers() {
        _cancelShowTimer()
        _cancelHideTimer()
        _cancelAutoHideTimer()
    }
    function _doOpen() {
        if (!_pendingShow) return
        toolTip.open()
    }

    objectName: "_toolTip"
    popupType: Popup.Window
    margins: -1
    leftPadding: Enums.spacing.l
    rightPadding: Enums.spacing.l
    topPadding: Enums.spacing.xs
    bottomPadding: Enums.spacing.xs
    closePolicy: Popup.NoAutoClose
    clip: false
    width: _tooltipTextWidth + leftPadding + rightPadding
    height: Math.max(Enums.controlSize.tooltipHeight, _tooltipText.implicitHeight + topPadding + bottomPadding)

    // ==================== Content 内容 ====================
    background: Rectangle {
        radius: Enums.radius.small
        color: Enums.cardColor
        border.width: Enums.border.thin
        border.color: Enums.stateColor.borderStrong
    }

    contentItem: Text {
        id: _tooltipText
        text: toolTip.widget.toolTipText
        font.pixelSize: Enums.typography.caption
        font.family: Enums.fontFamily
        color: Enums.foregroundColor
        wrapMode: Text.Wrap
        horizontalAlignment: toolTip.widget.toolTipTextAlignment
        verticalAlignment: Text.AlignVCenter
        width: toolTip._tooltipTextWidth
    }
    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0.0; to: 1.0; duration: Enums.duration.normal }
            NumberAnimation { property: "scale"; from: 0.8; to: 1.0; duration: Enums.duration.normal; easing.type: Easing.OutCubic }
        }
    }
    exit: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 1.0; to: 0.0; duration: Enums.duration.normal }
            NumberAnimation { property: "scale"; from: 1.0; to: 0.8; duration: Enums.duration.normal }
        }
    }

    TextMetrics {
        id: _tooltipMetrics
        text: toolTip.widget.toolTipText
        font.pixelSize: Enums.typography.caption
        font.family: Enums.fontFamily
    }

    Component {
        id: lifecycleTimerComponent

        Timer {
            id: lifecycleTimer

            required property int timerInterval
            required property var triggerCallback
            required property var releaseCallback

            interval: timerInterval
            onTriggered: {
                triggerCallback()
                releaseCallback(lifecycleTimer)
                destroy()
            }
        }
    }
}
