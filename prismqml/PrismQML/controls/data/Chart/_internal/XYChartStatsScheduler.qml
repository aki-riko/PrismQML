// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// XYChartStatsScheduler - Range-scan cache behind the scheduler gate 调度门控背后的范围扫描缓存
// Owns the cached value/scatter ranges, the dirty flag and the deferred rebuild
// used while the runtime scheduler gate is closed. XYChartCore keeps the public
// schedulerActive gate, the projection of these caches and the change wiring.
// 持有数值/散点范围缓存、脏标记与门控关闭期间的延迟重建; XYChartCore 保留公开
// schedulerActive 门控、缓存投影与变更接线。
Item {
    id: statsScheduler

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Internal Props 内部属性 ====================
    // Cache expensive range scans while inactive 停用期间缓存昂贵的范围扫描
    property var valueRangeCache: ({
        min: 0, max: 0, hasNegative: false, hasPositive: false
    })
    property var scatterRangeCache: ({ xMin: 0, xMax: 1, yMin: 0, yMax: 1 })
    property bool dirty: true
    property bool restorePending: false
    property int revision: 0

    // ==================== Internal Methods 内部方法 ====================
    function rebuild() {
        valueRangeCache = host._calculateValueRange()
        scatterRangeCache = host._calculateScatterDataRange()
        dirty = false
        revision++
    }

    function markDirty() {
        dirty = true
        if (!host.schedulerActive || restorePending) return
        rebuild()
    }

    function scheduleRestore() {
        restorePending = true
        restoreTimer.restart()
    }

    visible: false

    // ==================== Content 内容 ====================
    Timer {
        id: restoreTimer
        interval: 0
        repeat: false
        onTriggered: {
            statsScheduler.restorePending = false
            if (statsScheduler.host.schedulerActive && statsScheduler.dirty)
                statsScheduler.rebuild()
        }
    }
}
