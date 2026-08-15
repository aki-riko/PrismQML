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
