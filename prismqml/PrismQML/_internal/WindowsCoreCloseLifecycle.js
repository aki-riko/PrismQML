// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// WindowsCoreCloseLifecycle - Accepted close completion logic 已接受关闭的收尾逻辑

function completeAcceptedClose(host, frameLayer, transition, animationHelper) {
    if (!host._closeInProgress) return

    if (!host._closeHideOnlyLatched) {
        host._closeDesktopNotifications()
        // Keep the close gate up while Window.close() re-enters onClosing. 关闭重入时保持关闭门。
        var closed = host.close()
        if (closed === false) {
            host._cancelCloseRequest()
            return
        }
        // The host is restored only after the native window is off screen.
        // 只有原生窗口下屏后才还原宿主。
        transition.restoreHostWindow()
        host._closeInProgress = false
        host._closeCompletionPending = false
        host._closeHideOnlyLatched = false
        return
    }

    // Hide-only close keeps the window object and desktop notifications alive.
    // 隐藏式关闭保留窗口对象和桌面通知。
    host.hide()
    transition.restoreHostWindow()
    frameLayer.visible = host._closeSourceWasVisible
    animationHelper.restoreVisibleState()
    // Clear the gate last so hide() cannot restore paint state prematurely.
    // 最后清门，避免 hide() 期间提前恢复绘制状态。
    host._closeInProgress = false
    host._closeCompletionPending = false
    host._closeHideOnlyLatched = false
}
