// PopupPrewarm - Popup surface prewarm helpers 弹层表面预热辅助
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function prewarm(control, prewarmTimer) {
    if (control._prewarmed || control._prewarmScheduled || control.isOpen) return
    if (control.useInWindowPopup) {
        control._prewarmed = true
        return
    }
    if (!control.useQtPopupWindow && !control._ensureNativeWindow()) return
    control._prewarmScheduled = true
    prewarmTimer.start()
}

// Settle a queued prewarm synchronously before a press is handled.
// 在按下事件被处理之前，就地结算排队中的预热。
// The queued prewarm is a 0 ms timer, so input events win that race and a fast
// hover-then-click pays native surface creation plus the first show inside the
// click callback; settling it while the button is still down keeps the released
// click on the warm path.
// 预热排的是 0ms 定时器，会被输入事件抢先：快速 hover→点击会把建原生表面与首次
// show 的成本落在点击回调里；在按键仍按下时结算，抬起后的点击即走暖路径。
// Only the native surface path settles here; the Qt popup path would open and
// close an in-window surface and steal the focus of that same press.
// 这里只对原生表面路径生效；Qt 弹层模式会开关一次页内弹层并抢走这次按下的焦点。
function flushQueuedPrewarm(control, inlinePopup, prewarmTimer, qt, ownerWindow) {
    if (control._usesControlsPopup || control._prewarmed
            || control.isOpen || control.isClosing) return
    prewarm(control, prewarmTimer)
    if (control._prewarmScheduled)
        doPrewarm(control, inlinePopup, prewarmTimer, qt, ownerWindow)
}

function finishQtPopupPrewarm(control, inlinePopup, ownerWindow) {
    var focusItem = control._prewarmFocusItem
    control._prewarmingQtPopup = false
    control._prewarmFocusItem = null
    if (!control._prewarmScheduled || control.isOpen || inlinePopup.visible) return
    if (ownerWindow) ownerWindow.requestActivate()
    if (focusItem) focusItem.forceActiveFocus()
    control._prewarmed = true
    control._prewarmScheduled = false
}

function doPrewarm(control, inlinePopup, prewarmTimer, qt, ownerWindow) {
    if (control.useInWindowPopup) {
        control._prewarmed = true
        control._prewarmScheduled = false
        return
    }
    if (control.useQtPopupWindow) {
        if (!control._prewarmScheduled || control._prewarmed
                || control.isOpen || inlinePopup.visible) {
            if (inlinePopup.visible) control._prewarmed = true
            control._prewarmScheduled = false
            return
        }
        var savedInlineX = inlinePopup.x, savedInlineY = inlinePopup.y
        control._prewarmingQtPopup = true
        control._prewarmFocusItem = ownerWindow ? ownerWindow.activeFocusItem : null
        inlinePopup.x = -32000
        inlinePopup.y = -32000
        inlinePopup.open()
        inlinePopup.close()
        inlinePopup.x = savedInlineX
        inlinePopup.y = savedInlineY
        qt.callLater(control._finishQtPopupPrewarm)
        return
    }
    // A real open may win the race before this queued callback runs. 真正打开可能先于排队预热执行。
    // Never show+hide the menu in that case. 此时绝不能再 show+hide 把菜单藏掉。
    var nativeWindow = control._ensureNativeWindow()
    if (!nativeWindow) {
        control._prewarmScheduled = false
        return
    }
    if (!control._prewarmScheduled || control._prewarmed
            || control.isOpen || nativeWindow.visible) {
        if (nativeWindow.visible) control._prewarmed = true
        control._prewarmScheduled = false
        return
    }
    var savedX = nativeWindow.x, savedY = nativeWindow.y
    nativeWindow.x = -32000
    nativeWindow.y = -32000
    nativeWindow.show()
    nativeWindow.hide()
    nativeWindow.x = savedX
    nativeWindow.y = savedY
    control._prewarmed = true
    control._prewarmScheduled = false
}
