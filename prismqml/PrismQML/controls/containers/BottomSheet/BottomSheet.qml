// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../dialogs"
import "_internal" as SheetInternal

// BottomSheet - Bottom sheet overlay 底部弹层
// Slides up from the host bottom over a scrim; inherits OverlayDialogCore for
// reparenting to the window content item and scrim input blocking.
// 从宿主底部滑出并覆盖遮罩；继承 OverlayDialogCore 获得窗口级重挂载与遮罩输入拦截。
OverlayDialogCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int detent: Enums.sheet.detent_medium      // Resting height 停靠高度
    property int sheetMaxWidth: Enums.sheet.maxWidth    // Centered width cap 居中限宽
    default property alias content: sheetSurface.content
    // Qt-style state alias Qt风格状态别名
    property alias opened: control._isOpen

    // ==================== Readonly State 只读状态 ====================
    readonly property real sheetWidth: Math.min(width, sheetMaxWidth)
    readonly property real sheetHeight: detent === Enums.sheet.detent_large
        ? Math.max(0, height - Enums.sheet.topInset)
        : height * Enums.sheet.mediumRatio
    // Reveal progress: 0 hides the panel below the host, 1 rests it at the detent.
    // Driving a ratio instead of y keeps the first open correct after reparenting.
    // 显露进度：0 表示面板藏在宿主下方，1 表示停在停靠高度。驱动比例而不是 y，
    // 首次打开重挂载后起点仍然正确。
    readonly property real revealProgress: _revealProgress

    // ==================== Internal Props 内部属性 ====================
    property real _revealProgress: _isOpen ? 1 : 0

    // Overlay overrides 覆盖层配置
    dismissOnScrimClick: true
    maskColor: _skin.stateColor.dialogOverlay
    // The base hides on its restore timer, which is not tied to this slide-out;
    // stay visible until the panel has actually left the host.
    // 基类按恢复计时器隐藏，与本组件的滑出动画无关；保持可见直到面板真正离开宿主。
    visible: _isOpen || _isClosing || _revealProgress > 0

    // ==================== Content 内容 ====================
    SheetInternal.BottomSheetSurface {
        id: sheetSurface

        sheetControl: control
    }

    // Decelerate in, accelerate out 减速进入，加速离开
    Behavior on _revealProgress {
        NumberAnimation {
            duration: control._isOpen ? Enums.motionDuration.gentle
                                      : Enums.motionDuration.normal
            easing.type: Enums.motionTokens.easingType
            easing.bezierCurve: control._isOpen ? Enums.motionCurve.decelerate
                                                : Enums.motionCurve.accelerate
        }
    }
}
