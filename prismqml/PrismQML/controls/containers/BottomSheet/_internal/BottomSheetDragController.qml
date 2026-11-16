// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "BottomSheetGesture.js" as SheetGesture

// BottomSheetDragController - Turns grabber gestures into sheet state 把手柄手势转成弹层状态
// The finger writes height and reveal directly while dragging; the release picks the
// target and a velocity-matched duration, then hands back to the sheet's animations.
// 拖拽中由手指直接写入高度与显露进度；松手时选定目标与速度匹配时长，再交还弹层动画。
QtObject {
    id: drag

    // ==================== Required Props 必需属性 ====================
    required property var sheetControl

    // ==================== Internal Props 内部属性 ====================
    property real _startHeight: 0

    // ==================== Public Methods 公开方法 ====================
    function begin() {
        var sheet = drag.sheetControl
        sheet._heightAnimation.stop()
        sheet._releaseDuration = 0
        sheet._dragging = true
        drag._startHeight = sheet._revealProgress * sheet.sheetHeight
    }

    function moveTo(translationY) {
        var sheet = drag.sheetControl
        var detentHeight = sheet._detentHeight(sheet.detent)
        var maxHeight = sheet.allowLargeDetent
            ? sheet._detentHeight(Enums.sheet.detent_large) : detentHeight
        var state = SheetGesture.dragState(drag._startHeight, translationY, detentHeight,
                                           maxHeight, Enums.sheet.dragResistance)
        sheet._heightExtra = state.upExtension
        sheet._revealProgress = detentHeight > 0 ? 1 - state.downOffset / detentHeight : 0
    }

    function release(translationY, velocityY) {
        var sheet = drag.sheetControl
        var closeTarget = -1
        var target = SheetGesture.releaseTarget({
            detent: sheet.detent,
            translationY: translationY,
            velocityY: velocityY,
            detentHeight: sheet._detentHeight(sheet.detent),
            mediumHeight: sheet._detentHeight(Enums.sheet.detent_medium),
            largeHeight: sheet._detentHeight(Enums.sheet.detent_large),
            dismissRatio: Enums.sheet.dismissRatio,
            velocityThreshold: Enums.sheet.velocityThreshold,
            allowLargeDetent: sheet.allowLargeDetent,
            detentMedium: Enums.sheet.detent_medium,
            detentLarge: Enums.sheet.detent_large,
            closeTarget: closeTarget
        })
        var goal = target === closeTarget ? 0 : sheet._detentHeight(target)
        sheet._releaseDuration = SheetGesture.releaseDuration(
            sheet._revealProgress * sheet.sheetHeight - goal, velocityY,
            Enums.sheet.enterCurve, Enums.motionDuration.fast, Enums.motionDuration.slow)
        sheet._dragging = false
        if (target === closeTarget) {
            sheet._heightAnimation.stop()
            sheet.close()
            // Slide out from the dragged position 从拖到的位置继续滑出
            sheet._revealProgress = Qt.binding(function() { return sheet._isOpen ? 1 : 0 })
        } else if (target !== sheet.detent) {
            sheet.detent = target
        } else {
            sheet._settle()
        }
        // Not cleared here: the running animation's duration and curve are bindings, and
        // clearing now would switch them mid-flight. The sheet clears it when they finish.
        // 不在此清零：运行中动画的时长与曲线是绑定，此时清零会在中途切换；由弹层在动画结束时清零。
    }
}
