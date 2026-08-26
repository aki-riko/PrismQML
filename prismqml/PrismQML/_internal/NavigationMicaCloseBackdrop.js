// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// Mica is a DWM hwnd-level material, so the close circle's QML layer mask cannot reach
// it. Left on, DWM keeps filling the whole window rect and the periphery the circle just
// clipped still shows Mica — measured #f0f4f9 at every progress on a real machine. Same
// category as the native DWM shadow: drop it for the close collapse only.
// Mica 是 DWM hwnd 级材质, 关闭圆环的 QML layer 遮罩到不了它。不撤掉的话 DWM 仍按整窗
// 矩形填充, 圆刚裁掉的外围照样是 Mica — 真机实测每一帧都是 #f0f4f9。与原生 DWM 阴影
// 同类: 仅在关闭收紧期间撤掉。
//
// micaManager and isDark are passed in because a .pragma library has no QML context and
// cannot see the MicaManager singleton or Enums.
// micaManager 与 isDark 由外部传入: .pragma library 没有 QML 上下文, 看不到
// MicaManager 单例和 Enums。
function apply(host, collapsing, micaManager, isDark) {
    if (!micaManager || !host._micaActive || !host._nativeHookReady)
        return false
    if (!collapsing) {
        // Cancelled close must put the backdrop back, or the window stays on screen
        // without Mica. 取消关闭必须把背板装回, 否则窗口留在屏上却没了 Mica。
        return host._applyMicaEffect("closeCancelled")
    }
    // No pending reapply timer needs stopping here: NavigationMicaReapplyTimer triggers
    // _applyMicaEffect, which refuses while _closeInProgress. Their ids are unreachable
    // from a .pragma library anyway.
    // 无需在此停掉待重试定时器: NavigationMicaReapplyTimer 触发的是 _applyMicaEffect,
    // 它在 _closeInProgress 时会拒绝。且 .pragma library 里本就取不到它们的 id。
    // Order matters. _micaTransparent is _micaActive && _micaBackdropReady and it drives
    // windowColor, so clearing the flag is what flips the frame fill opaque. Dropping the
    // backdrop first left one composited frame with no DWM material *and* a still-transparent
    // fill — the window flashed see-through before turning opaque. Clear the flag first so
    // the opaque fill is already queued when the material goes.
    // 顺序有讲究。_micaTransparent 是 _micaActive && _micaBackdropReady, 它驱动
    // windowColor, 所以清掉标志才是让窗框填充变不透明的动作。先撤背板会留下一帧
    // 「无 DWM 材质 + 填充仍透明」, 于是窗口先闪一下透视再变不透明。先清标志, 让不透明
    // 填充在材质消失时已经排上。
    host._micaBackdropReady = false
    host.requestUpdate()
    var ok = micaManager.setMicaEffect(host, false, isDark)
    // setMicaEffect writes DWMWCP_ROUND even when disabling, so restore the native
    // corner. 即使是关闭, setMicaEffect 也会写入 DWMWCP_ROUND, 故恢复原生边角。
    host._syncNativeCorner("mica:closeCollapse")
    return ok
}
