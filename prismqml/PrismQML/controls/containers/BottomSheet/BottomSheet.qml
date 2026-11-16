// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../dialogs"
import "_internal" as SheetInternal
import "../../utils"

// BottomSheet - Bottom sheet overlay 底部弹层
// Slides up from the host bottom over a scrim; inherits OverlayDialogCore for
// reparenting to the window content item and scrim input blocking.
// 从宿主底部滑出并覆盖遮罩；继承 OverlayDialogCore 获得窗口级重挂载与遮罩输入拦截。
OverlayDialogCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int detent: Enums.sheet.detent_medium      // Resting height 停靠高度
    property bool allowLargeDetent: true                // Drag or tap up to large 允许上拉或点按展开
    property bool showGrabber: true                     // Top drag handle 顶部拖拽手柄
    property real sheetWidthRatio: Enums.sheet.widthRatio   // Width / host width 宽度占宿主比例
    default property alias content: sheetSurface.content
    // Qt-style state alias Qt风格状态别名
    property alias opened: control._isOpen

    // ==================== Readonly State 只读状态 ====================
    readonly property real sheetWidth: width * Math.max(0, Math.min(1, sheetWidthRatio))
    // Detent height plus the transient drag/settle extension 停靠高度加拖拽/回弹中的临时伸长
    readonly property real sheetHeight: _detentHeight(detent) + _heightExtra
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
    property real _heightExtra: 0
    property bool _dragging: false
    property bool _settling: false   // Immediate writes while true 为真时直接写入不走动画
    // Velocity-matched duration for the animations one release starts; cleared once they
    // finish. 一次松手所启动动画的速度匹配时长；动画结束后清零。
    property int _releaseDuration: 0
    property int _previousDetent: Enums.sheet.detent_medium
    // Handles for the internal drag controller 供内部拖拽控制器使用的句柄
    readonly property var _drag: dragController
    readonly property var _heightAnimation: heightAnimation
    readonly property var _sheetAbove: SheetInternal.BottomSheetStack.above(
        control, SheetInternal.BottomSheetStack.openSheets)
    readonly property real _restTop: height - sheetHeight
    readonly property real _revealTop: height - _revealProgress * sheetHeight
    // Peek above the sheet on top, never past the host top 从上层上方露边，不越过宿主顶部
    readonly property real _coveredTop: _sheetAbove
        ? Math.max(0, Math.min(_restTop, _sheetAbove.panelTop) - Enums.sheet.stackPeek)
        : _restTop

    // ==================== Public Methods 公开方法 ====================
    function expand() { if (allowLargeDetent) detent = Enums.sheet.detent_large }
    function collapse() { detent = Enums.sheet.detent_medium }

    // ==================== Internal Methods 内部方法 ====================
    function _detentHeight(value) {
        return value === Enums.sheet.detent_large
            ? Math.max(0, height - Enums.sheet.topInset)
            : height * Enums.sheet.mediumRatio
    }

    // Settle on the current detent from wherever the panel is, keeping its top edge
    // still at the switch. Only one of height or reveal moves afterwards, so the
    // settle never reverses direction.
    // 从面板当前位置平滑停到当前 detent，切换瞬间顶边不动。之后只有高度或显露其中之一
    // 在变，回弹不会折返。
    function _settle() {
        var previous = _detentHeight(_previousDetent) + _heightExtra
        _previousDetent = detent
        heightAnimation.stop()
        if (!_isOpen) {
            _heightExtra = 0
            return
        }
        var shown = _revealProgress * previous
        var target = _detentHeight(detent)
        _settling = true
        _heightExtra = Math.max(0, shown - target)
        _revealProgress = target > 0 ? Math.min(1, shown / target) : 1
        _settling = false
        _revealProgress = Qt.binding(function() { return control._isOpen ? 1 : 0 })
        heightAnimation.restart()
    }

    // A release may start both animations; clear once neither is running.
    // 一次松手可能同时启动两段动画，两者都结束后再清零。
    function _clearReleaseDuration() {
        if (!heightAnimation.running && !revealAnimation.running) _releaseDuration = 0
    }

    function _toggleDetent() {
        if (detent === Enums.sheet.detent_large) collapse()
        else expand()
    }

    // Keyboard goes to the top sheet; closing hands it back to the one below.
    // 键盘焦点交给栈顶弹层；关闭后交还给下一层。
    function _focusTop() {
        var top = SheetInternal.BottomSheetStack.topOf(control.parent,
            SheetInternal.BottomSheetStack.openSheets)
        if (top) top.forceActiveFocus()
    }

    // Overlay overrides 覆盖层配置
    dismissOnScrimClick: true
    // The base scrim keeps only its input blocking; BottomSheetSurface draws a scrim that
    // follows the reveal. 基类遮罩只保留输入拦截；由 BottomSheetSurface 绘制跟随显露进度的遮罩。
    maskColor: _skin.transparent
    z: _skin.zIndex.modal + Math.max(0, stackIndex + 1) * Enums.sheet.stackZStep
    // The base hides on its restore timer, which is not tied to this slide-out;
    // stay visible until the panel has actually left the host.
    // 基类按恢复计时器隐藏，与本组件的滑出动画无关；保持可见直到面板真正离开宿主。
    visible: _isOpen || _isClosing || _revealProgress > 0
    Accessible.role: AccessibilityHelper.roleValue(Enums.accessibility.role_dialog)

    // Escape closes the top sheet only: lower sheets never hold the focus.
    // Escape 只关闭栈顶弹层：下层弹层不会持有焦点。
    Keys.onEscapePressed: (event) => {
        event.accepted = true
        control.close()
    }
    onDetentChanged: _settle()
    Component.onCompleted: _previousDetent = detent
    onOpenedChanged: {
        if (control._isOpen) {
            SheetInternal.BottomSheetStack.push(control)
            // After the open reparenting settles 等打开时的重挂载稳定后再取焦点
            Qt.callLater(control._focusTop)
        } else {
            // Nested sheets close with their parent 嵌套子层随父层一起关闭
            SheetInternal.BottomSheetStack.closeNested(control)
            if (control.activeFocus) Qt.callLater(control._focusTop)
        }
    }
    onRevealProgressChanged: {
        if (!control._isOpen && control._revealProgress === 0) {
            SheetInternal.BottomSheetStack.remove(control)
            // A drag-dismissed sheet may leave a stretch behind 拖拽关闭可能残留伸长量
            heightAnimation.stop()
            control._heightExtra = 0
        }
    }
    Component.onDestruction: SheetInternal.BottomSheetStack.remove(control)

    // ==================== Content 内容 ====================
    SheetInternal.BottomSheetSurface {
        id: sheetSurface

        sheetControl: control
    }

    SheetInternal.BottomSheetDragController {
        id: dragController

        sheetControl: control
    }

    NumberAnimation {
        id: heightAnimation

        target: control
        property: "_heightExtra"
        to: 0
        duration: control._releaseDuration || Enums.motionDuration.slow
        easing.type: Enums.motionTokens.easingType
        easing.bezierCurve: Enums.sheet.enterCurve
        onFinished: control._clearReleaseDuration()
    }

    // Glide in, ease out; a release continues at the finger's speed and decelerates.
    // The finger drives it directly while dragging.
    // 平缓滑入、柔和离开；松手后以手指速度接续再减速。拖拽期间由手指直接驱动。
    // Duration and curve follow the Behavior's targetValue, which is set before the
    // animation starts. Reading _isOpen instead raced the _revealProgress binding:
    // measured on a real window, opens ran the exit curve and closes the enter curve.
    // 时长与曲线跟随 Behavior 的 targetValue，它在动画启动前设置。改读 _isOpen 会与
    // _revealProgress 的绑定竞争：真实窗口实测打开用了离开曲线、关闭用了进入曲线。
    Behavior on _revealProgress {
        id: revealBehavior

        enabled: !control._dragging && !control._settling
        NumberAnimation {
            id: revealAnimation

            readonly property bool entering: revealBehavior.targetValue > 0

            duration: control._releaseDuration
                || (entering ? Enums.motionDuration.slow : Enums.motionDuration.gentle)
            easing.type: Enums.motionTokens.easingType
            easing.bezierCurve: entering || control._releaseDuration > 0
                ? Enums.sheet.enterCurve : Enums.sheet.exitCurve
            onFinished: control._clearReleaseDuration()
        }
    }
}
