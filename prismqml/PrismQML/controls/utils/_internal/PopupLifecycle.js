// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// PopupLifecycle - Shared popup surface lifecycle state machine
// 弹层 surface 共享生命周期状态机

function _timer(control) {
    return control._lifecycleTimer
}

function beginOpen(control) {
    if (control.isClosing) return false
    if (control.isOpen) return true
    // Repeated open requests can arrive while the surface is still completing
    // its first show timer. Keep the lifecycle idempotent but let the caller
    // refresh the requested position instead of dropping that geometry update.
    // 首次显示计时器尚未完成时可能收到重复 open 请求；生命周期仍保持幂等，
    // 但允许调用方刷新目标位置，不能丢弃这次几何更新。
    if (control._openRequested) return true
    control._openRequested = true
    control._surfaceRecoveryAttemptCount = 0
    return true
}

function scheduleCompletion(control) {
    if (!control._openRequested || control.isClosing) return
    _timer(control).start()
}

function canClose(control, surfaceVisible) {
    return !control.isClosing
        && (control._openRequested || control.isOpen
            || _timer(control).running || surfaceVisible)
}

function beginClose(control) {
    control._openRequested = false
    control._surfaceRecoveryAttemptCount = 0
    control._surfaceRecoveryScheduled = false
    _timer(control).stop()
    control.isOpen = false
    control.isClosing = true
}

function forceReset(control) {
    control._openRequested = false
    control._surfaceRecoveryAttemptCount = 0
    control.isOpen = false
    control.isClosing = false
    _resetOpenState(control)
}

function handleSurfaceClosed(control) {
    // Ignore a queued close notification that belongs to an older surface
    // instance and arrived after the replacement surface is visible again.
    // 忽略旧 surface 的延迟关闭通知，避免重开后的新 surface 被误复位。
    if (control._surfaceVisible) return
    if (control.isClosing || !control._openRequested) return
    if (!control.isOpen) {
        _timer(control).stop()
        control._resetOpenAppearance()
        _scheduleRecovery(control)
        return
    }
    control._openRequested = false
    control._surfaceRecoveryAttemptCount = 0
    control.isOpen = false
    control.isClosing = false
    _resetOpenState(control)
    control.closed()
}

function _resetOpenState(control) {
    _timer(control).stop()
    control._surfaceRecoveryScheduled = false
    control._resetOpenAppearance()
}

function _abortPendingOpen(control) {
    var shouldNotifyClosed = control._openRequested
    control._openRequested = false
    control._surfaceRecoveryAttemptCount = 0
    control.isOpen = false
    control.isClosing = false
    _resetOpenState(control)
    if (shouldNotifyClosed) control.closed()
}

function _scheduleRecovery(control) {
    if (!control._openRequested || control.isClosing
            || control.isOpen || control._surfaceRecoveryScheduled) return
    if (control._surfaceRecoveryAttemptCount >= control._maxSurfaceRecoveryAttempts) {
        _abortPendingOpen(control)
        return
    }
    control._surfaceRecoveryScheduled = true
    _timer(control).start()
}

function _retrySurfaceOpen(control) {
    control._surfaceRecoveryScheduled = false
    if (!control._openRequested || control.isClosing || control.isOpen) return
    if (!control._surfaceVisible) {
        control._surfaceRecoveryAttemptCount += 1
        control._showCurrentSurface()
    }
    if (!control._openRequested || control.isClosing || control.isOpen) return
    _timer(control).start()
}

function _completeOpen(control) {
    if (!control._openRequested || control.isClosing || control.isOpen) return
    if (!control._surfaceVisible) {
        _scheduleRecovery(control)
        return
    }
    _timer(control).stop()
    control._surfaceRecoveryScheduled = false
    control._surfaceRecoveryAttemptCount = 0
    control.isOpen = true
    // Publishing isOpen before the native capture hand-off makes any
    // synchronous surface close re-enter the "already open" path. The guards
    // below prevent that re-entrant close from being overwritten by the rest
    // of this completion callback.
    // 先发布 isOpen，使原生捕获交接期间同步关闭走“已打开”路径；下方守卫
    // 防止重入关闭后又被当前完成回调覆盖。
    control._releaseQtPopupCapture()
    if (!control._openRequested || control.isClosing
            || !control.isOpen || !control._surfaceVisible) return
    control._startOpenAnimation()
    if (!control._openRequested || control.isClosing
            || !control.isOpen || !control._surfaceVisible) return
    control.opened()
}

function onTimer(control) {
    if (control._surfaceRecoveryScheduled) _retrySurfaceOpen(control)
    else _completeOpen(control)
}
