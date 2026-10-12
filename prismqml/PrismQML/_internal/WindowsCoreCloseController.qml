// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// WindowsCoreCloseController - Owns the window close handshake 窗口关闭握手的实现所有者
QtObject {
    id: controller

    // ==================== Required Props 必需属性 ====================
    required property var hostWindow
    required property var frameLayer
    required property var animationHelper
    required property var transition
    required property var frameWaiter

    // ==================== Internal Methods 内部方法 ====================
    function cancelRequest() {
        hostWindow._closeInProgress = false
        hostWindow._closeCompletionPending = false
        hostWindow._closeHideOnlyLatched = false
        frameWaiter.cancel()
        // stop() also restores this window's opacity if the overlay path hid it.
        // stop() 同时会在覆盖窗口那条路藏了本窗口时把不透明度还原。
        transition.stop()
        frameLayer.visible = hostWindow._closeSourceWasVisible
        if (hostWindow.visible) {
            animationHelper.restoreVisibleState()
        }
    }
    function startAcceptedClose() {
        hostWindow._closeInProgress = true
        hostWindow._closeHideOnlyLatched = hostWindow.closeRequestHideOnly
        hostWindow._closeSourceWasVisible = frameLayer.visible
        // Nothing hwnd-level is dropped here on purpose. The collapse runs in the overlay
        // window (preferOverlayWindow), which has no Mica and no native shadow, and this
        // window is hidden by opacity once the overlay's mask frame is up — so there is
        // nothing left for a drop to accomplish. Dropping was also the flash itself: writing
        // DWMWA_SYSTEMBACKDROP_TYPE makes DWM recompose visibly. Isolated on a real machine
        // with a throwaway flag that dropped one effect per run — only the Mica variant
        // flashed. Offscreen tests cannot see this, so the gates for it are static.
        // 这里故意不撤任何 hwnd 级效果。收紧是在覆盖窗口里跑的(preferOverlayWindow), 那个
        // 窗口既没 Mica 也没原生阴影, 而本窗口在覆盖窗遮罩帧上屏后就被 opacity 藏了 ——
        // 所以撤除已无事可做。撤除本身就是闪烁源: 写 DWMWA_SYSTEMBACKDROP_TYPE 会让 DWM
        // 可见地重新合成。真机上用一次性开关逐个撤效果隔离过, 只有撤 Mica 那次会闪。
        // offscreen 测试看不到这个现象, 所以相关门禁只能是静态的。
        transition.collapse(frameLayer)
    }
    function completeAcceptedClose() {
        if (!hostWindow._closeInProgress) return
        if (!hostWindow._closeHideOnlyLatched) {
            closeDesktopNotifications()
            // A close only hides this window; the object and the engine stay alive, so the close
            // state still has to be rewound after it — otherwise _closeInProgress latches
            // forever: it keeps ensureVisiblePaintState from restoring paint state and makes
            // every later requestClose/onClosing take the "already closing" branch, so the
            // window could never be closed again. The rewind must stay after window.close():
            // the close request is still on the stack while the platform delivers it, and that
            // delivery re-enters onClosing. With the gate still up it lands on
            // nativeCloseAccepted, which is the same step it has always taken; dropping the
            // gate first would make it replay a whole second collapsed close.
            // 关闭只是把这个窗口藏起来, 对象与引擎都还活着, 因此关闭之后仍必须复位关闭状态,
            // 否则 _closeInProgress 会永久闩住: 它既挡住 ensureVisiblePaintState 恢复绘制状态,
            // 又让之后每次 requestClose/onClosing 都走「关闭中」分支, 窗口再也关不掉。复位必须
            // 留在 window.close() 之后: 平台投递这次关闭时它仍在调用栈上, 那次投递会重入
            // onClosing; 门还立着才落到 nativeCloseAccepted —— 与历来的一步完全相同。先落门
            // 则会让它把整个带动画关闭再播一遍。
            var closed = hostWindow.close()
            if (closed === false) {
                cancelRequest()
                return
            }
            // The overlay path hid this window to keep its Mica out of the collapsing circle.
            // Restore it only now that the close succeeded and the window is off screen —
            // restoring any earlier shows one frame of the full, un-collapsed window.
            // 覆盖窗口那条路把本窗口藏了, 好让它的 Mica 不出现在收缩圆里。只有现在关闭已成功、
            // 窗口已下屏才还原 —— 早一点还原就会露出一帧完整的、没收紧的窗口。
            transition.restoreHostWindow()
            hostWindow._closeInProgress = false
            hostWindow._closeCompletionPending = false
            hostWindow._closeHideOnlyLatched = false
            return
        }
        // Hide-only close: the collapse already played in the overlay window, so
        // finish by hiding instead of destroying, then rewind every piece of close
        // state so the window can be shown and closed again later. Like the real
        // close above, the host is only restored once the window is off screen.
        // 隐藏式关闭: 收缩动画已在覆盖窗口播完，这里以隐藏代替销毁收尾，并把关闭
        // 状态全部复位，窗口之后仍可再次显示与关闭。与真实关闭一致, 宿主窗口
        // 必须等已下屏后才还原。
        // Desktop notifications are deliberately not closed here, unlike the real close
        // above: hiding is the collapse-to-tray path, not a shutdown, so notifications the
        // user has not dismissed yet stay alive and dismissible. Only a destroyed window
        // has to sweep them away.
        // 这里故意不像上面的真实关闭那样关掉桌面通知: 隐藏是收进托盘, 不是退出, 用户尚未
        // 处理的通知应当继续存活并可被处理。只有即将销毁的窗口才必须把它们清掉。
        hostWindow.hide()
        transition.restoreHostWindow()
        frameLayer.visible = hostWindow._closeSourceWasVisible
        animationHelper.restoreVisibleState()
        // Cleared last: _closeInProgress must still gate onVisibleChanged ->
        // ensureVisiblePaintState while the hide() above runs, or the just-hidden window
        // would have its paint state restored a frame early.
        // 最后才复位: 上面那次 hide() 触发 onVisibleChanged 时, _closeInProgress 必须仍然挡住
        // ensureVisiblePaintState, 否则刚下屏的窗口会提前一帧被恢复绘制状态。
        hostWindow._closeInProgress = false
        hostWindow._closeCompletionPending = false
        hostWindow._closeHideOnlyLatched = false
    }
    function armAcceptedClose() {
        if (!hostWindow._closeInProgress) return
        hostWindow._closeCompletionPending = true
        frameWaiter.arm()
    }
    function handleCloseFrameEnd() {
        if (!hostWindow._closeCompletionPending) return
        hostWindow._closeCompletionPending = false
        Qt.callLater(hostWindow._completeAcceptedClose)
    }
    function closeDesktopNotifications() {
        var component = Qt.createComponent(Qt.resolvedUrl("DesktopNotificationCloser.qml"))
        if (component.status !== Component.Ready) {
            console.warn("DesktopNotificationCloser not ready:", component.errorString())
            return
        }
        var closer = component.createObject(hostWindow)
        if (!closer) return
        closer.closeAll()
        closer.destroy()
    }
}
