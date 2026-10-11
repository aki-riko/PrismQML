// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../../.."

// IncrementalLoadTrigger - Near-end incremental loading gate 接近末尾的增量加载门
// Raises loadRequested() once the viewport gets within triggerDistance of the content
// end, then stays quiet until the consumer calls complete(). Re-arming waits for the
// view to remeasure the appended rows, so one batch is requested at a time.
// 视口进入内容末尾 triggerDistance 内时发出一次 loadRequested(), 之后保持静默直到消费方
// 调用 complete()。重新武装会等待视图重测新增行, 因此每次只请求一个批次。
QtObject {
    id: trigger

    // ==================== Public Props 公开属性 ====================
    property var viewport: null
    property bool enabled: false
    property int itemCount: 0
    // Rows requested per batch 每批请求的行数
    property int batchSize: 20
    // Distance from the content end that still counts as "near the end" 视为接近末尾的距离
    property real triggerDistance: 0

    // ==================== Internal Props 内部属性 ====================
    property bool _loading: false
    property real _epsilon: Enums.scroll.boundary_epsilon
    property QtObject _viewportConnections: Connections {
        function onContentYChanged() { trigger._evaluate() }
        function onContentHeightChanged() { trigger._evaluate() }
        function onHeightChanged() { trigger._evaluate() }

        target: trigger.viewport
        ignoreUnknownSignals: true
    }

    // ==================== Readonly State 只读状态 ====================
    readonly property bool isLoading: trigger._loading

    // ==================== Signals 信号 ====================
    signal loadRequested(int batchSize)

    // ==================== Public Methods 公开方法 ====================
    // Called by the consumer once the requested batch has been appended.
    // 消费方在追加完所请求的批次后调用。
    function complete() {
        if (!trigger._loading) return
        trigger._loading = false
        // A filled viewport must wait for the view to remeasure the appended rows:
        // the still-stale content height would otherwise request a second batch.
        // 已填满的视口必须等视图重测新增行, 否则仍然过期的内容高度会再要一批。
        var target = trigger.viewport
        if (target && target.contentHeight <= target.height + trigger._epsilon) {
            trigger._evaluate()
        }
    }

    // ==================== Internal Methods 内部方法 ====================
    function _distanceToEnd() {
        var target = trigger.viewport
        if (!target) return 0
        return Math.max(0, target.contentHeight - (target.contentY + target.height))
    }

    function _evaluate() {
        if (!trigger.enabled || trigger._loading || !trigger.viewport) return
        if (trigger.itemCount < 0) return
        var distance = trigger._distanceToEnd()
        var limit = trigger.triggerDistance
        // A mis-wired viewport or limit must never turn into a request storm.
        // 视口或阈值接线错误绝不能演变成请求风暴。
        if (!isFinite(distance) || !isFinite(limit)) return
        if (distance > limit) return
        trigger._loading = true
        trigger.loadRequested(trigger.batchSize)
    }

    onEnabledChanged: trigger._evaluate()
    onItemCountChanged: {
        // A growing count only moves the end further away, and the view may still
        // report the previous content height. Re-evaluate only while the viewport
        // still has empty space to fill.
        // 计数增长只会让末尾更远, 且视图可能仍报告上一版内容高度; 仅在视口仍有空白时重估。
        var target = trigger.viewport
        if (target && target.contentHeight <= target.height + trigger._epsilon) {
            trigger._evaluate()
        }
    }
    onViewportChanged: trigger._evaluate()
    onTriggerDistanceChanged: trigger._evaluate()
}
