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
    if (control._openRequested) return false
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
    control._releaseQtPopupCapture()
    control.isOpen = true
    control._startOpenAnimation()
    control.opened()
}

function onTimer(control) {
    if (control._surfaceRecoveryScheduled) _retrySurfaceOpen(control)
    else _completeOpen(control)
}
