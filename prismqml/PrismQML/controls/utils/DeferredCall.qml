// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// DeferredCall - Deferred call whose lifetime follows its host 随宿主销毁的延迟调用
//
// Qt.callLater() queues its callback inside the engine, so destroying the target object does
// not cancel it. When that callback finally runs, the target's QML context may already be
// invalid: Qt then reports "attempted to evaluate a function in an invalid context" and every
// QML method on that object resolves to undefined, which surfaces as
// "Property 'xxx' ... is not a function".
// Declare this object inside the object that owns the deferred work. Its pending actions then
// die together with the host, so a callback can never outlive the objects it touches.
// The deferred tick is pinned to "once, on the next event-loop iteration"; do not override
// interval or repeat.
//
// Qt.callLater() 的回调由引擎排队，销毁目标对象并不会取消它；回调真正执行时，目标的 QML
// 上下文可能已经失效，Qt 会报 "attempted to evaluate a function in an invalid context"，使该
// 对象上所有 QML 方法解析为 undefined，最终表现为 "Property 'xxx' ... is not a function"。
// 把本对象声明在「拥有这次延迟动作」的对象内部，待执行动作便随宿主一起销毁，
// 回调不可能比它操作的对象活得更久。延迟节奏固定为「下一帧执行一次」，不要覆盖 interval
// 与 repeat。
//
// Usage 用法:
//   Item {
//       DeferredCall { id: deferred }
//
//       onContentChanged: deferred.call(syncLayout)                // dedupe by function
//       onFilterChanged: deferred.coalesce("reload", loadLatest)   // latest snapshot only
//   }
Item {
    id: control

    // ==================== Internal Props 内部属性 ====================
    // Pending entries, each one shaped as a key plus an action 待执行项：key + action
    property var _entries: []
    // Shared with an active drain after QML object teardown. 销毁后仍供当前 drain 读取。
    property var _lifetime: ({ alive: true })

    // ==================== Readonly State 只读状态 ====================
    readonly property int pendingCount: _entries.length

    // ==================== Public Methods 公开方法 ====================
    // Queue one action for the next event-loop tick. Re-scheduling the same function object
    // while it is still pending collapses into a single run, which matches Qt.callLater().
    // Actions never receive extra arguments; capture data in a closure instead.
    // 把动作排到下一帧。同一函数对象在待执行期间重复入队会合并为一次，与 Qt.callLater() 一致；
    // 动作不接收附加参数，需要数据时请用闭包捕获。
    function call(action) {
        if (!_isAction(action)) {
            console.warn("DeferredCall.call requires a function")
            return
        }
        if (_indexOfAction(action) >= 0) return
        // Reassign instead of push: a var property only notifies on assignment, and
        // pendingCount must stay observable. 必须整体赋值，就地 push 不会触发属性通知。
        _entries = _entries.concat([{ key: "", action: action }])
        tick.restart()
    }

    // Keep only the latest action of one key. Use it when the action closure captures
    // changing data and only the newest snapshot may run.
    // 同一 key 只保留最后一次：适合闭包捕获了变化数据、只允许最新快照执行的场景。
    function coalesce(key, action) {
        if (!_isAction(action)) {
            console.warn("DeferredCall.coalesce requires a function")
            return
        }
        var name = _keyName(key)
        if (name === "") {
            console.warn("DeferredCall.coalesce requires a non-empty key")
            return
        }
        var next = _withoutKey(name)
        next.push({ key: name, action: action })
        _entries = next
        tick.restart()
    }

    // Drop the pending action of one key. 丢弃某个 key 的待执行动作。
    function cancel(key) {
        var name = _keyName(key)
        if (_indexOfKey(name) < 0) return
        _entries = _withoutKey(name)
        if (_entries.length === 0) tick.stop()
    }

    // Drop every pending action. 丢弃全部待执行动作。
    function cancelAll() {
        _entries = []
        tick.stop()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _isAction(action) {
        return typeof action === "function"
    }

    function _keyName(key) {
        return key === undefined || key === null ? "" : String(key)
    }

    function _indexOfAction(action) {
        for (var index = 0; index < _entries.length; index++) {
            if (_entries[index].action === action) return index
        }
        return -1
    }

    function _indexOfKey(key) {
        for (var index = 0; index < _entries.length; index++) {
            if (_entries[index].key === key) return index
        }
        return -1
    }

    function _withoutKey(key) {
        var remaining = []
        for (var index = 0; index < _entries.length; index++) {
            if (_entries[index].key !== key) remaining.push(_entries[index])
        }
        return remaining
    }

    function _drain() {
        if (_entries.length === 0) return
        var pending = _entries
        var lifetime = _lifetime
        _entries = []
        for (var index = 0; index < pending.length; index++) {
            // An earlier action may synchronously destroy the host.
            // 前一个动作可能同步销毁宿主，此时不得调用后续闭包。
            if (!lifetime.alive) return
            try {
                pending[index].action()
            } catch (error) {
                console.warn("DeferredCall: deferred action failed -", String(error))
            }
        }
    }

    Component.onDestruction: _lifetime.alive = false

    // Deferred tick contract: one run on the next event-loop iteration
    // 延迟节奏契约：下一帧执行一次
    Timer {
        id: tick

        interval: 0
        repeat: false

        onTriggered: control._drain()
    }
}
