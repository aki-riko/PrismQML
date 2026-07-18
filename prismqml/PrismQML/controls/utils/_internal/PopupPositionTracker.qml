// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// PopupPositionTracker - Event-driven popup anchor tracker 事件驱动弹层锚点跟踪器
Item {
    id: tracker

    // ==================== Required Props 必需属性 ====================
    required property var target
    required property var targetWindow
    required property bool trackingEnabled
    required property real positionEpsilon

    // ==================== Internal Props 内部属性 ====================
    property point _lastGlobalPosition: Qt.point(-1, -1)
    property bool _updatePending: false

    // ==================== Signals 信号 ====================
    signal targetMoved(point globalPosition)
    signal targetOutOfView()

    // ==================== Internal Methods 内部方法 ====================
    function scheduleUpdate() {
        if (!trackingEnabled || !target || _updatePending) return
        _updatePending = true
        Qt.callLater(function() {
            tracker._updatePending = false
            tracker._updatePosition()
        })
    }

    function _updatePosition() {
        if (!trackingEnabled || !target) return

        var currentGlobalPosition = target.mapToGlobal(0, 0)
        if (Math.abs(currentGlobalPosition.x - _lastGlobalPosition.x) < positionEpsilon &&
            Math.abs(currentGlobalPosition.y - _lastGlobalPosition.y) < positionEpsilon) {
            return
        }
        _lastGlobalPosition = currentGlobalPosition

        if (targetWindow && target.mapToItem !== undefined && targetWindow.contentItem) {
            var localPosition = target.mapToItem(targetWindow.contentItem, 0, 0)
            if (localPosition.y < -target.height || localPosition.y > targetWindow.height ||
                localPosition.x < -target.width || localPosition.x > targetWindow.width) {
                targetOutOfView()
                return
            }
        }
        targetMoved(currentGlobalPosition)
    }

    visible: false

    onTargetChanged: {
        _lastGlobalPosition = Qt.point(-1, -1)
        scheduleUpdate()
    }
    onTargetWindowChanged: scheduleUpdate()
    onTrackingEnabledChanged: scheduleUpdate()

    // Follow direct target geometry changes without polling 目标几何变化时事件驱动跟随
    Connections {
        function onXChanged() { tracker.scheduleUpdate() }
        function onYChanged() { tracker.scheduleUpdate() }
        function onWidthChanged() { tracker.scheduleUpdate() }
        function onHeightChanged() { tracker.scheduleUpdate() }
        function onVisibleChanged() { tracker.scheduleUpdate() }
        function onParentChanged() { tracker.scheduleUpdate() }

        target: tracker.trackingEnabled ? tracker.target : null
        ignoreUnknownSignals: true
    }

    // Ancestor scrolling renders a frame; native window movement emits geometry signals.
    // 祖先滚动会渲染新帧，原生窗口移动会发出几何信号。
    Connections {
        function onAfterAnimating() { tracker.scheduleUpdate() }
        function onXChanged() { tracker.scheduleUpdate() }
        function onYChanged() { tracker.scheduleUpdate() }
        function onWidthChanged() { tracker.scheduleUpdate() }
        function onHeightChanged() { tracker.scheduleUpdate() }

        target: tracker.trackingEnabled ? tracker.targetWindow : null
        ignoreUnknownSignals: true
    }
}
