// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

pragma Singleton
import QtQuick

// HeavyComponentScheduler - Shared admission queue for expensive QML content 重型 QML 内容共享准入队列
// The scheduler controls creation admission only. Consumers opt into runtime
// pausing through HeavyComponentSlot.workActive.
// 调度器只控制创建准入；组件是否暂停运行由 HeavyComponentSlot.workActive 显式决定。
Item {
    id: scheduler

    visible: false
    width: 0
    height: 0

    // ==================== Public Props 公开属性 ====================
    readonly property int priority_background: 10
    readonly property int priority_prefetch: 30
    readonly property int priority_visible: 60
    readonly property int priority_interaction: 100
    property bool schedulerEnabled: true
    property int tickInterval: 16
    property int activationBudgetMs: 5
    property int maxActivationsPerTick: 1

    // ==================== Internal Props 内部属性 ====================
    property var _slots: []
    property int _sequence: 0
    property bool _timerEnabled: false

    // ==================== Signals 信号 ====================
    signal slotActivated(var slot)

    // ==================== Internal Methods 内部方法 ====================
    function registerSlot(slot) {
        if (!slot || _slots.indexOf(slot) >= 0) return
        slot._schedulerSequence = _sequence++
        _slots = _slots.concat([slot])
    }

    function unregisterSlot(slot) {
        var index = _slots.indexOf(slot)
        if (index < 0) return
        var next = _slots.slice()
        next.splice(index, 1)
        _slots = next
        _refreshTimer()
    }

    function requestActivation(slot) {
        if (!slot) return
        registerSlot(slot)
        slot._schedulerRequested = true
        _timerEnabled = true
    }

    function cancelActivation(slot) {
        if (!slot) return
        slot._schedulerRequested = false
        _refreshTimer()
    }

    function _canActivate(slot) {
        return slot && slot._schedulerRequested &&
                slot._schedulerCanActivate() && slot._schedulerNeedsActivation()
    }

    function _compareSlots(left, right) {
        if (left.priority !== right.priority) return right.priority - left.priority
        return left._schedulerSequence - right._schedulerSequence
    }

    function _dispatch() {
        var candidates = []
        for (var i = 0; i < _slots.length; i++) {
            if (_canActivate(_slots[i])) candidates.push(_slots[i])
        }
        candidates.sort(_compareSlots)

        var limit = Math.max(1, maxActivationsPerTick)
        var budget = Math.max(1, activationBudgetMs)
        var startedAt = Date.now()
        var activated = 0
        for (var index = 0; index < candidates.length && activated < limit; index++) {
            if (activated > 0 && Date.now() - startedAt >= budget) break
            if (candidates[index]._schedulerActivate()) {
                activated += 1
                candidates[index]._schedulerRequested = false
                slotActivated(candidates[index])
            }
        }
        _refreshTimer()
    }

    function _refreshTimer() {
        var pending = false
        for (var i = 0; i < _slots.length; i++) {
            if (_canActivate(_slots[i])) {
                pending = true
                break
            }
        }
        _timerEnabled = pending
    }

    Timer {
        id: dispatchTimer

        interval: Math.max(1, scheduler.tickInterval)
        repeat: true
        running: scheduler.schedulerEnabled && scheduler._timerEnabled
        onTriggered: scheduler._dispatch()
    }
}
