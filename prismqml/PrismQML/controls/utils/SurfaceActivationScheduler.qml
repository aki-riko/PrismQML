// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

pragma Singleton
import QtQuick

// SurfaceActivationScheduler - Completion-aware admission for native surfaces
// 原生表面的完成感知准入调度器
Item {
    id: scheduler

    visible: false
    width: 0
    height: 0

    // ==================== Public Props 公开属性 ====================
    property bool enabled: true
    property int tickInterval: 16
    property int maxConcurrentPerGroup: 1
    property int maxActivationsPerTick: 1
    readonly property int pendingCount: _queue.length
    readonly property int activeCount: _active.length

    // ==================== Internal Props 内部属性 ====================
    property var _queue: []
    property var _active: []
    property int _sequence: 0

    // ==================== Signals 信号 ====================
    signal activationStarted(var surface, string group)
    signal activationFinished(var surface, string group)

    // ==================== Public Methods 公开方法 ====================
    function request(surface, group) {
        if (!surface || !group) return false
        if (_isActive(surface) || _queueIndex(surface) >= 0) return true
        surface._surfaceActivationQueued = true
        _queue = _queue.concat([{
            "surface": surface,
            "group": String(group),
            "sequence": _sequence++
        }])
        return true
    }

    function cancel(surface) {
        var index = _queueIndex(surface)
        if (index < 0) return false
        var next = _queue.slice()
        next.splice(index, 1)
        _queue = next
        if (surface) surface._surfaceActivationQueued = false
        return true
    }

    function release(surface) {
        cancel(surface)
        var index = _activeIndex(surface)
        if (index < 0) return false
        var entry = _active[index]
        var next = _active.slice()
        next.splice(index, 1)
        _active = next
        if (surface) surface._surfaceActivationActive = false
        activationFinished(surface, entry.group)
        return true
    }

    function activeCountForGroup(group) {
        var count = 0
        for (var i = 0; i < _active.length; i++) {
            if (_active[i].group === group) count++
        }
        return count
    }

    function queuedCountForGroup(group) {
        var count = 0
        for (var i = 0; i < _queue.length; i++) {
            if (_queue[i].group === group) count++
        }
        return count
    }

    // ==================== Internal Methods 内部方法 ====================
    function _queueIndex(surface) {
        for (var i = 0; i < _queue.length; i++) {
            if (_queue[i].surface === surface) return i
        }
        return -1
    }

    function _activeIndex(surface) {
        for (var i = 0; i < _active.length; i++) {
            if (_active[i].surface === surface) return i
        }
        return -1
    }

    function _isActive(surface) {
        return _activeIndex(surface) >= 0
    }

    function _dispatch() {
        if (!enabled || _queue.length === 0) return
        var queue = _queue.slice()
        var started = 0
        for (var i = 0; i < queue.length && started < maxActivationsPerTick; i++) {
            var entry = queue[i]
            if (activeCountForGroup(entry.group) >= maxConcurrentPerGroup) continue
            if (!entry.surface || !entry.surface._surfaceCanActivate()) {
                cancel(entry.surface)
                continue
            }

            cancel(entry.surface)
            entry.surface._surfaceActivationActive = true
            _active = _active.concat([entry])
            var accepted = entry.surface._surfaceActivate()
            if (!accepted) {
                release(entry.surface)
                continue
            }
            started++
            activationStarted(entry.surface, entry.group)
        }
    }

    Timer {
        interval: Math.max(1, scheduler.tickInterval)
        repeat: true
        running: scheduler.enabled && scheduler._queue.length > 0
        onTriggered: scheduler._dispatch()
    }
}
