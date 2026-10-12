// NavigationWindowMica - Mica application and rescheduling Mica 应用与重调度
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function apply(window, reason, manager, isDark, backdropCommitTimer) {
    // A reapply during collapse would repaint Mica outside the closing circle.
    // 折叠期间重应用会让 Mica 在收缩圆外重绘。
    if (!manager || !window._micaAvailable || !window._nativeHookReady
            || (window._closeInProgress && reason !== "closeCancelled")) {
        window._micaNativeApplySucceeded = false
        window._micaBackdropReady = false
        return false
    }
    window.profileTime("NavigationWindowCore apply Mica " + reason + " start")
    var success = manager.setMicaEffect(window, window._micaActive, isDark)
    // Mica writes DWMWCP_ROUND even when disabling, so restore the QML frame corner.
    // 即使关闭背板，Mica 也会写 DWMWCP_ROUND，因此恢复为 QML 窗框圆角。
    window._syncNativeCorner("mica:" + reason)
    window._micaNativeApplySucceeded = success
    window._micaBackdropReady = false
    backdropCommitTimer.stop()
    if (window._micaActive && success) backdropCommitTimer.restart()
    window.profileTime(
        "NavigationWindowCore apply Mica " + reason + " done success=" + success
    )
    return success
}

function scheduleReapply(window, reason, backdropCommitTimer, reapplyTimer, lateReapplyTimer) {
    if (!window._micaActive || !window._nativeHookReady || window._closeInProgress)
        return
    // Hide the transparent fallback until DWM confirms the backdrop again.
    // DWM 再次确认背板前先关闭透明兜底，避免只剩透明外壳。
    window._micaBackdropReady = false
    backdropCommitTimer.stop()
    window._micaReapplyReason = reason
    reapplyTimer.restart()
    lateReapplyTimer.restart()
}
