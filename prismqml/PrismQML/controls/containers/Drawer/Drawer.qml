// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import "../../.."
import "../../dialogs"
import "_internal" as DrawerInternal

// Drawer - Drawer component 抽屉组件
// Inherits OverlayDialogCore for overlay functionality 继承OverlayDialogCore获得覆盖功能
// Place as Window direct child, auto cover entire window 放在Window子级自动覆盖窗口
OverlayDialogCore {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int mode: Enums.drawer.mode_inside  // Inside/outside placement 内侧/外侧放置模式
    property int position: Enums.position.right
    property int drawerWidth: 320
    property int drawerHeight: 400
    property bool modal: true  // Inside mode scrim only 仅控制内侧模式遮罩
    /// Drawer slide-in/out animation duration in ms (default matches global slow; 抽屉滑入/滑出动画时长 (毫秒)。默认与全局慢速一致;
    /// 紧凑场景可调小,例如 200。
    property int animationDuration: Enums.duration.slow
    property bool nativeDialogOpen: false
    default property alias content: drawerSurface.content
    readonly property bool isHorizontal: position === Enums.position.left || position === Enums.position.right
    
    // Qt-style state alias Qt风格状态别名
    property alias opened: control._isOpen

    // Panel corner radius 面板圆角
    property int radius: _isOutside
        ? Enums.radius.large
        : (Enums.radius.none)
    // ==================== Internal Props 内部属性 ====================
    property bool _outsideFollowRegistered: false
    property bool _outsideHostSyncPending: false
    property bool _outsidePrepared: false
    property bool _outsideResetting: false
    property bool _outsideVisible: false
    property bool _outsideNativeShadowCleared: false
    property real _outsideExtent: _outsideCollapsedExtent
    property bool _insideAnimationReady: false
    property bool _insideOpenPending: false
    // Delay window signal wiring until every V4 method is finalized. 延迟窗口信号连接，直到所有 V4 方法完成终结。
    property var _hostSignalTarget: null

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isOutside: mode === Enums.drawer.mode_outside
    readonly property var _hostWindow: control.Window.window
    readonly property int _outsideCollapsedExtent: Enums.border.thin
    readonly property real _outsideFullExtent: isHorizontal ? drawerWidth : drawerHeight
    // Outward padding reserved inside the follower HWND for the drawer's own window shadow.
    // 附属 HWND 内侧为抽屉自绘窗口阴影预留的外扩留白。
    readonly property real _outsideShadowSpread: Enums.shadow.windowOutside.blur
    readonly property real _outsideWindowExtent: _outsideFullExtent + _outsideShadowSpread
    // The outward shadow only exists once the full panel is revealed.
    // 只有在面板完全显露后才有外侧阴影。
    readonly property bool _outsideShadowActive: _outsidePrepared && _isOpen
        && !outsideGeometryAnimation.running
    readonly property color _drawerBackground: Enums.cardColor
    readonly property int _effectiveRadius: Enums.surfaceRadius(radius)
    readonly property real _drawerBorderWidth: Enums.hasOutlinedSurfaces
                                               ? Enums.surfaceBorderWidth(Enums.border.thin) : 0
    readonly property color _drawerBorderColor: Enums.hasOutlinedSurfaces
                                                 ? Enums.stateColor.border : Enums.transparent
    readonly property var _outsideDrawerWindow: outsideDrawerWindowLoader.item
    readonly property var _outsideDrawerPanel: _outsideDrawerWindow ? _outsideDrawerWindow.panel : null

    // ==================== Public Methods 公开方法 ====================
    // Override open to use base class mechanism 重写open使用基类机制
    function open() {
        // Save original parent 保存原始父组件
        if (!_originalParent) {
            _originalParent = control.parent
        }

        // Rebase the first inside opening to the window edge before animating
        // 首次内侧打开先按窗口边缘重定位,再启动动画
        if (!control._isOutside && control.Window && control.Window.window) {
            var windowContent = control.Window.window.contentItem
            if (windowContent && control.parent !== windowContent) {
                if (control._insideOpenPending) return
                control._insideOpenPending = true
                control._insideAnimationReady = false
                control.parent = windowContent
                Qt.callLater(control._completeInsideOpen)
                return
            }
        }

        if (control._isOutside) {
            if (control._isOpen) return
            if (control._outsideVisible && !control._outsidePrepared) return
            _isClosing = false
            outsideGeometryAnimation.stop()
            if (!control._outsideVisible) {
                control._unregisterOutsideWindow()
                control._outsidePrepared = false
                control._outsideExtent = control._outsideCollapsedExtent
                control._updateOutsideWindowGeometry()
                control._outsideVisible = true
                return
            }
            control._isOpen = true
            control._startOutsideAnimation(control._outsideFullExtent)
            return
        }
        _isClosing = false
        _isOpen = true
    }

    function toggle() { _isOpen ? close() : open() }

    function isOpen() {
        return _isOpen
    }

    function suspendForNativeDialog() { if (_isOutside && !nativeDialogOpen) nativeDialogOpen = true }
    function resumeAfterNativeDialog() { if (nativeDialogOpen) nativeDialogOpen = false }
    function _completeInsideOpen() {
        if (!control._insideOpenPending) return
        control._insideOpenPending = false
        control._insideAnimationReady = true
        if (!control._isOutside) {
            control._isClosing = false
            control._isOpen = true
        }
    }

    // Reset both render paths when switching mode or closing the host window
    // 切换模式或宿主窗口关闭时重置两条渲染路径
    function _resetDrawerState() {
        outsideGeometryAnimation.stop()
        _clearOutsideNativeShadow()
        _unregisterOutsideWindow()
        _outsideResetting = true
        _outsideVisible = false
        _outsidePrepared = false
        _outsideExtent = _outsideCollapsedExtent
        _outsideHostSyncPending = false
        _insideOpenPending = false
        _insideAnimationReady = true
        _isOpen = false
        _isClosing = false
        _outsideResetting = false
        if (control._isOutside && control._hostWindow
                && control._hostWindow.visible) {
            control._updateOutsideWindowGeometry()
        }
    }

    // Animate only the clip extent; the HWND and content keep their final geometry
    // 只动画裁剪范围,HWND 与内容始终保持最终几何
    function _startOutsideAnimation(targetExtent) {
        outsideGeometryAnimation.stop()
        outsideGeometryAnimation.from = control._outsideExtent
        outsideGeometryAnimation.to = targetExtent
        if (control.animationDuration <= 0
                || control._outsideExtent === targetExtent) {
            control._outsideExtent = targetExtent
            control._finishOutsideAnimation()
            return
        }
        outsideGeometryAnimation.start()
    }

    // Correct Qt's post-show geometry once, then reveal the fixed window
    // 在 Qt 完成 show 后校正一次几何,随后再显露固定窗口
    function _beginOutsideReveal() {
        if (!control._isOutside || !control._outsideVisible
                || control.nativeDialogOpen) return
        if (control._outsidePrepared && control._isOpen) {
            control._updateOutsideWindowGeometry()
            control._registerOutsideWindow()
            return
        }
        if (control._outsidePrepared || control._isOpen) return
        control._updateOutsideWindowGeometry()
        control._outsidePrepared = true
        control._registerOutsideWindow()
        control._isOpen = true
        control._startOutsideAnimation(control._outsideFullExtent)
    }

    // Register native edge following for the visible outside window
    // 为可见外侧窗口注册原生边缘跟随
    function _registerOutsideWindow() {
        if (!control._isOutside || !control._hostWindow
                || !_outsideDrawerWindow || !_outsideDrawerWindow.visible
                || typeof WindowHelper === "undefined" || !WindowHelper) return
        control._outsideFollowRegistered = WindowHelper.registerWindowFollower(
            control._hostWindow,
            _outsideDrawerWindow,
            control.position,
            control._outsideWindowExtent,
            true,
            control._outsideShadowSpread)
    }

    // Remove the native follower before hiding or destruction
    // 在隐藏或销毁前移除原生跟随
    function _unregisterOutsideWindow() {
        if (_outsideDrawerWindow
                && typeof WindowHelper !== "undefined" && WindowHelper) {
            WindowHelper.unregisterWindowFollower(_outsideDrawerWindow)
        }
        control._outsideFollowRegistered = false
    }

    // Submit position and size together with one native geometry call
    // 通过一次原生几何调用同时提交位置与尺寸
    function _updateOutsideWindowGeometry() {
        if (!control._isOutside || !control._hostWindow
                || !_outsideDrawerWindow
                || typeof WindowHelper === "undefined" || !WindowHelper) return false
        return WindowHelper.updateWindowFollowerGeometry(
            control._hostWindow,
            _outsideDrawerWindow,
            control.position,
            control._outsideWindowExtent,
            control._outsideShadowSpread)
    }

    // Coalesce host geometry notifications outside the drawer animation
    // 在抽屉动画以外合并宿主几何通知
    function _scheduleOutsideHostSync() {
        if (!control._isOutside || !control._outsideVisible
                || control._outsideHostSyncPending) return
        control._outsideHostSyncPending = true
        Qt.callLater(control._flushOutsideHostSync)
    }

    function _flushOutsideHostSync() {
        control._outsideHostSyncPending = false
        if (control._isOutside && control._outsideVisible
                && control._outsidePrepared) {
            control._updateOutsideWindowGeometry()
        }
    }

    // Finish visibility and following from the real animation lifecycle
    // 根据真实动画生命周期收尾可见性与窗口跟随
    function _finishOutsideAnimation() {
        if (!control._isOutside || control._outsideResetting
                || !control._outsideVisible) return
        if (outsideGeometryAnimation.running) return
        if (control._isOpen) {
            if (!control._outsideFollowRegistered) {
                control._registerOutsideWindow()
            }
            return
        }
        control._unregisterOutsideWindow()
        control._outsideVisible = false
        control._outsidePrepared = false
    }

    // Keep native antialiasing; DWM corners stay square so the QML shadow keeps its shape
    // 保留原生抗锯齿; DWM 圆角保持直角, 避免裁掉 QML 阴影与接缝侧的方角
    function _applyOutsideNativeFrame() {
        if (_outsideDrawerWindow
                && typeof MicaManager !== "undefined" && MicaManager) {
            MicaManager.setWindowCorner(_outsideDrawerWindow, false)
        }
    }

    // The HWND keeps no DWM shadow: the seam-side band would land on the host window
    // 该 HWND 始终不带 DWM 阴影: 否则接缝侧的阴影带会压到宿主窗口上
    function _clearOutsideNativeShadow() {
        if (control._outsideNativeShadowCleared || !_outsideDrawerWindow
                || typeof ShadowManager === "undefined" || !ShadowManager) return
        if (ShadowManager.disableShadowForWindow(_outsideDrawerWindow)) {
            control._outsideNativeShadowCleared = true
        }
    }

    // Overlay overrides 覆盖层配置
    dismissOnScrimClick: modal  // Close when scrim is clicked in modal mode 模态时点击遮罩关闭
    maskColor: !_isOutside && modal ? Enums.stateColor.dialogOverlay : Enums.transparent
    visible: !_isOutside && (_isOpen || _isClosing)

    onModeChanged: _resetDrawerState()
    Component.onCompleted: {
        control._insideAnimationReady = true
        control._hostSignalTarget = Qt.binding(function() { return control._hostWindow })
    }
    onOpenedChanged: {
        if (!control._isOutside || control._outsideResetting) return
        if (!control._isOpen && control._outsideVisible) {
            control._clearOutsideNativeShadow()
            control._startOutsideAnimation(control._outsideCollapsedExtent)
        }
    }
    onPositionChanged: {
        if (control._isOutside) {
            control._unregisterOutsideWindow()
            control._updateOutsideWindowGeometry()
            if (control._outsideVisible && control._outsidePrepared) {
                control._registerOutsideWindow()
            }
        }
    }

    // ==================== Content 内容 ====================
    // Native host for the outside mode 外侧模式的原生承载窗口
    Loader {
        id: outsideDrawerWindowLoader
        property var drawerControl: control

        active: control._isOutside
        asynchronous: false
        onItemChanged: control._outsideNativeShadowCleared = false
        sourceComponent: Component {
            DrawerInternal.DrawerOutsideWindow {
                drawerControl: outsideDrawerWindowLoader.drawerControl
            }
        }
    }

    NumberAnimation {
        id: outsideGeometryAnimation

        target: control
        property: "_outsideExtent"
        duration: control.animationDuration
        easing.type: Easing.OutCubic
        onFinished: control._finishOutsideAnimation()
    }

    // Inside drawer visual layer 内侧抽屉视觉层
    DrawerInternal.DrawerSurface {
        id: drawerSurface

        anchors.fill: parent
        drawerControl: control
    }

    Connections {
        function onClosing(close) { control._resetDrawerState() }
        function onXChanged() { control._scheduleOutsideHostSync() }
        function onYChanged() { control._scheduleOutsideHostSync() }
        function onWidthChanged() { control._scheduleOutsideHostSync() }
        function onHeightChanged() { control._scheduleOutsideHostSync() }
        function onActiveChanged() { control._scheduleOutsideHostSync() }
        function onVisibilityChanged() {
            if (control._isOutside && control._hostWindow
                    && control._hostWindow.visibility === Window.Hidden) {
                control._resetDrawerState()
            } else if (control._isOutside && control._hostWindow
                       && control._hostWindow.visibility !== Window.Minimized
                       && control._outsideVisible && control._outsidePrepared) {
                control._updateOutsideWindowGeometry()
                control._registerOutsideWindow()
            }
        }
        function onVisibleChanged() {
            if (control._isOutside && control._hostWindow
                    && !control._hostWindow.visible) {
                control._resetDrawerState()
            }
        }

        target: control._hostSignalTarget
        ignoreUnknownSignals: true
    }
}
