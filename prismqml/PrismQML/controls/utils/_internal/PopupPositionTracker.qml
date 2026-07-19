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

    // ==================== Signals 信号 ====================
    signal targetMoved(point globalPosition)
    signal targetOutOfView()

    // ==================== Internal Methods 内部方法 ====================
    function scheduleUpdate() {
        if (!trackingEnabled || !target || updateTimer.running) return
        updateTimer.start()
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

    // Coalesce geometry signals while keeping queued work bound to this lifecycle.
    // 合并几何信号，并让待执行任务跟随当前对象生命周期销毁。
    Timer {
        id: updateTimer

        interval: 0
        repeat: false
        onTriggered: tracker._updatePosition()
    }

    // Delay QQmlConnections creation until the popup is actively tracking.
    // 仅在弹层实际跟踪时创建QQmlConnections，避开异步孵化期的Qt连接竞态。
    Loader {
        id: connectionLoader

        active: tracker.trackingEnabled && tracker.target !== null
        asynchronous: false
        sourceComponent: Item {
            visible: false

            // Follow direct target geometry changes without polling 目标几何变化时事件驱动跟随
            Connections {
                function onXChanged() { tracker.scheduleUpdate() }
                function onYChanged() { tracker.scheduleUpdate() }
                function onWidthChanged() { tracker.scheduleUpdate() }
                function onHeightChanged() { tracker.scheduleUpdate() }
                function onVisibleChanged() { tracker.scheduleUpdate() }
                function onParentChanged() { tracker.scheduleUpdate() }

                target: tracker.target
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

                target: tracker.targetWindow
                ignoreUnknownSignals: true
            }
        }
    }
}
