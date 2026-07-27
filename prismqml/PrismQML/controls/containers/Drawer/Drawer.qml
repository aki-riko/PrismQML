// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import QtQuick.Effects
import "../../.."
import "../../../effects"
import "../../dialogs"

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
    /// 抽屉滑入/滑出动画时长 (毫秒)。默认与全局慢速一致;
    /// 紧凑场景可调小,例如 200。
    property int animationDuration: Enums.duration.slow
    default property alias content: contentItem.data
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
    property real _outsideExtent: _outsideCollapsedExtent
    property bool _insideAnimationReady: false
    property bool _insideOpenPending: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isOutside: mode === Enums.drawer.mode_outside
    readonly property var _hostWindow: control.Window.window
    readonly property int _outsideCollapsedExtent: Enums.border.thin
    readonly property real _outsideFullExtent: isHorizontal ? drawerWidth : drawerHeight
    readonly property color _drawerBackground: Enums.cardColor
    readonly property int _drawerBorderWidth: Enums.isNeobrutalism ? Enums.neo.borderWidth : (0)
    readonly property color _drawerBorderColor: Enums.isNeobrutalism ? Enums.stateColor.border : (Enums.transparent)

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

    // Check if open 检查是否打开
    function isOpen() {
        return _isOpen
    }

    // Start the first inside animation after reparenting geometry has settled
    // 重父化几何稳定后再启动首次内侧动画
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
        _setOutsideNativeShadow(false)
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
                || control._outsidePrepared || control._isOpen) return
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
                || !outsideDrawerWindow.visible
                || typeof WindowHelper === "undefined" || !WindowHelper) return
        control._outsideFollowRegistered = WindowHelper.registerWindowFollower(
            control._hostWindow,
            outsideDrawerWindow,
            control.position,
            control._outsideFullExtent)
    }

    // Remove the native follower before hiding or destruction
    // 在隐藏或销毁前移除原生跟随
    function _unregisterOutsideWindow() {
        if (outsideDrawerWindow
                && typeof WindowHelper !== "undefined" && WindowHelper) {
            WindowHelper.unregisterWindowFollower(outsideDrawerWindow)
        }
        control._outsideFollowRegistered = false
    }

    // Submit position and size together with one native geometry call
    // 通过一次原生几何调用同时提交位置与尺寸
    function _updateOutsideWindowGeometry() {
        if (!control._isOutside || !control._hostWindow
                || !outsideDrawerWindow
                || typeof WindowHelper === "undefined" || !WindowHelper) return false
        return WindowHelper.updateWindowFollowerGeometry(
            control._hostWindow,
            outsideDrawerWindow,
            control.position,
            control._outsideFullExtent)
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
            control._setOutsideNativeShadow(true)
            return
        }
        control._setOutsideNativeShadow(false)
        control._unregisterOutsideWindow()
        control._outsideVisible = false
        control._outsidePrepared = false
    }

    // Keep native antialiasing; QML still limits panel rounding to the outer corners
    // 保留原生抗锯齿,面板仍仅由 QML 设置远离宿主的两个外角
    function _applyOutsideNativeFrame() {
        if (outsideDrawerWindow
                && typeof MicaManager !== "undefined" && MicaManager) {
            MicaManager.setWindowCorner(outsideDrawerWindow, true)
        }
    }

    // Hide the full-size HWND shadow while only part of its content is revealed
    // 内容仅部分显露时隐藏完整尺寸 HWND 的阴影
    function _setOutsideNativeShadow(enabled) {
        if (!outsideDrawerWindow
                || typeof ShadowManager === "undefined" || !ShadowManager) return
        if (enabled) {
            ShadowManager.enableShadowForWindow(outsideDrawerWindow)
        } else {
            ShadowManager.disableShadowForWindow(outsideDrawerWindow)
        }
    }

    // Overlay overrides 覆盖层配置
    dismissOnScrimClick: modal  // Close when scrim is clicked in modal mode 模态时点击遮罩关闭
    maskColor: !_isOutside && modal ? Enums.stateColor.dialogOverlay : Enums.transparent
    visible: !_isOutside && (_isOpen || _isClosing)

    onModeChanged: _resetDrawerState()
    Component.onCompleted: control._insideAnimationReady = true
    onOpenedChanged: {
        if (!control._isOutside || control._outsideResetting) return
        if (!control._isOpen && control._outsideVisible) {
            control._setOutsideNativeShadow(false)
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
    Window {
        id: outsideDrawerWindow
        readonly property bool horizontal: control.isHorizontal

        objectName: "outsideDrawerWindow"
        x: 0
        y: 0
        width: control.drawerWidth
        height: control.drawerHeight
        visible: control._isOutside && control._outsideVisible
            && control._hostWindow !== null
        opacity: control._outsidePrepared ? 1 : 0
        flags: Qt.Tool | Qt.FramelessWindowHint
        color: Enums.transparent
        transientParent: null

        onVisibleChanged: {
            if (visible) {
                control._applyOutsideNativeFrame()
                control._setOutsideNativeShadow(false)
                Qt.callLater(control._beginOutsideReveal)
            } else {
                control._unregisterOutsideWindow()
            }
        }
        onActiveChanged: {
            if (active && control._outsidePrepared) {
                control._scheduleOutsideHostSync()
            }
        }
        onClosing: (close) => control._resetDrawerState()
        Component.onDestruction: control._unregisterOutsideWindow()

        Item {
            id: outsideDrawerViewport
            objectName: "outsideDrawerViewport"

            x: control.position === Enums.position.left
                ? (outsideDrawerWindow ? outsideDrawerWindow.width : 0) - width
                : 0
            y: control.position === Enums.position.top
                ? (outsideDrawerWindow ? outsideDrawerWindow.height : 0) - height
                : 0
            width: control.isHorizontal
                ? Math.min(control._outsideExtent,
                    outsideDrawerWindow ? outsideDrawerWindow.width : 0)
                : (outsideDrawerWindow ? outsideDrawerWindow.width : 0)
            height: control.isHorizontal
                ? (outsideDrawerWindow ? outsideDrawerWindow.height : 0)
                : Math.min(control._outsideExtent,
                    outsideDrawerWindow ? outsideDrawerWindow.height : 0)
            clip: true

            Rectangle {
                id: outsideDrawerPanel
                objectName: "outsideDrawerPanel"

                width: outsideDrawerWindow ? outsideDrawerWindow.width : 0
                height: outsideDrawerWindow ? outsideDrawerWindow.height : 0
                x: outsideDrawerViewport ? -outsideDrawerViewport.x : 0
                y: outsideDrawerViewport ? -outsideDrawerViewport.y : 0
                color: control._drawerBackground
                radius: Enums.radius.none
                topLeftRadius: control.position === Enums.position.left
                    || control.position === Enums.position.top
                    ? control.radius : Enums.radius.none
                topRightRadius: control.position === Enums.position.right
                    || control.position === Enums.position.top
                    ? control.radius : Enums.radius.none
                bottomLeftRadius: control.position === Enums.position.left
                    || control.position === Enums.position.bottom
                    ? control.radius : Enums.radius.none
                bottomRightRadius: control.position === Enums.position.right
                    || control.position === Enums.position.bottom
                    ? control.radius : Enums.radius.none
                border.width: control._drawerBorderWidth
                border.color: control._drawerBorderColor

                MouseArea {
                    anchors.fill: parent
                }
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

    // Drawer shadow 抽屉阴影
    // Shadow for drawer 抽屉阴影
    RectangularShadow {
        anchors.fill: drawer
        radius: control.radius
        color: Enums.shadow.level28.color
        blur: Enums.shadow.level28.blur
        offset.x: 0
        offset.y: Enums.shadow.level28.offset
        visible: control._isOpen || control._isClosing
    }
    
    // Drawer panel 抽屉面板
    Rectangle {
        id: drawer

        readonly property real effectiveWidth: control.width > 0 ? control.width : (control.parent ? control.parent.width : 0)
        readonly property real effectiveHeight: control.height > 0 ? control.height : (control.parent ? control.parent.height : 0)

        color: control._drawerBackground
        radius: control.radius
        // Drawer boundary for non-Fluent skins 非 Fluent 皮肤抽屉边界
        border.width: control._drawerBorderWidth
        border.color: control._drawerBorderColor
        
        // Use parent size directly when control size is 0 (Python setParentItem timing issue) 当 control 尺寸为 0 时直接使用 parent 尺寸（Python setParentItem 时序问题）

        width: isHorizontal ? control.drawerWidth : effectiveWidth
        height: isHorizontal ? effectiveHeight : control.drawerHeight

        // Block clicks from reaching the overlay mask 阻止点击穿透到遮罩层
        MouseArea {
            anchors.fill: parent
            // Consume all clicks so they don't propagate to the mask 消费点击防止穿透
        }
        
        // Use states to manage position 使用states管理位置
        states: [
            State {
                name: "open"
                when: control._isOpen
                PropertyChanges {
                    target: drawer
                    x: position === Enums.position.left ? 0 : 
                       (position === Enums.position.right ? drawer.effectiveWidth - drawer.width : 0)
                    y: position === Enums.position.top ? 0 :
                       (position === Enums.position.bottom ? drawer.effectiveHeight - drawer.height : 0)
                }
            },
            State {
                name: "closed"
                when: !control._isOpen
                PropertyChanges {
                    target: drawer
                    x: position === Enums.position.left ? -drawer.width :
                       (position === Enums.position.right ? drawer.effectiveWidth : 0)
                    y: position === Enums.position.top ? -drawer.height :
                       (position === Enums.position.bottom ? drawer.effectiveHeight : 0)
                }
            }
        ]

        transitions: Transition {
            enabled: control._insideAnimationReady
            NumberAnimation { properties: "x,y"; duration: control.animationDuration; easing.type: Easing.OutCubic }
        }
    }

    // Shared content host moves between inside and outside panels
    // 共享内容宿主在内侧与外侧面板间移动
    Item {
        id: contentItem
        objectName: "contentItem"  // For Python findChild 供Python查找

        parent: control._isOutside ? outsideDrawerPanel : drawer
        anchors.fill: parent
        anchors.margins: Enums.spacing.xl

        // Clear input focus when clicking empty content area 点击内容空白处清除输入焦点
        MouseArea {
            anchors.fill: parent
            z: Enums.zIndex.background
            onClicked: contentItem.forceActiveFocus()
        }
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
                    && (control._hostWindow.visibility === Window.Hidden
                        || control._hostWindow.visibility === Window.Minimized)) {
                control._resetDrawerState()
            }
        }
        function onVisibleChanged() {
            if (control._isOutside && control._hostWindow
                    && !control._hostWindow.visible) {
                control._resetDrawerState()
            }
        }

        target: control._hostWindow
        ignoreUnknownSignals: true
    }
}
