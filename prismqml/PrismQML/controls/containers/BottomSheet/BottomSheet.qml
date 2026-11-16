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
    // Position in the host stack, bottom first; -1 once fully closed. A closing sheet
    // keeps its slot until it has slid out, so the sheets below settle back with it.
    // 在宿主栈中的位置，自底向上；完全关闭后为 -1。关闭中的弹层在滑出前保留位置，
    // 下层随它一起平滑复位。
    readonly property int stackIndex: SheetInternal.BottomSheetStack.indexOf(
        control, SheetInternal.BottomSheetStack.openSheets)
    // Covering levels, fractional while the sheet above slides 被覆盖层数，上层滑动时为小数
    readonly property real stackLift: _sheetAbove
        ? _sheetAbove.stackLift + _sheetAbove.revealProgress : 0
    // Panel top edge in host coordinates 面板顶边（宿主坐标）
    readonly property real panelTop: _sheetAbove
        ? _revealTop + (_coveredTop - _restTop) * _sheetAbove.revealProgress
        : _revealTop

    // ==================== Internal Props 内部属性 ====================
    property real _revealProgress: _isOpen ? 1 : 0
    readonly property var _sheetAbove: SheetInternal.BottomSheetStack.above(
        control, SheetInternal.BottomSheetStack.openSheets)
    readonly property real _restTop: height - sheetHeight
    readonly property real _revealTop: height - _revealProgress * sheetHeight
    // Peek above the sheet on top, never past the host top 从上层上方露边，不越过宿主顶部
    readonly property real _coveredTop: _sheetAbove
        ? Math.max(0, Math.min(_restTop, _sheetAbove.panelTop) - Enums.sheet.stackPeek)
        : _restTop

    // Overlay overrides 覆盖层配置
    dismissOnScrimClick: true
    // Only the bottom sheet dims the page, so stacking never darkens it further.
    // 只有最底层弹层压暗页面，叠多少层背景亮度都不变。
    maskColor: stackIndex <= 0 ? _skin.stateColor.dialogOverlay : _skin.transparent
    z: _skin.zIndex.modal + Math.max(0, stackIndex + 1) * Enums.sheet.stackZStep
    // The base hides on its restore timer, which is not tied to this slide-out;
    // stay visible until the panel has actually left the host.
    // 基类按恢复计时器隐藏，与本组件的滑出动画无关；保持可见直到面板真正离开宿主。
    visible: _isOpen || _isClosing || _revealProgress > 0

    onOpenedChanged: {
        if (control._isOpen) {
            SheetInternal.BottomSheetStack.push(control)
        } else {
            // Nested sheets close with their parent 嵌套子层随父层一起关闭
            SheetInternal.BottomSheetStack.closeNested(control)
        }
    }
    onRevealProgressChanged: {
        if (!control._isOpen && control._revealProgress === 0) {
            SheetInternal.BottomSheetStack.remove(control)
        }
    }
    Component.onDestruction: SheetInternal.BottomSheetStack.remove(control)

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
