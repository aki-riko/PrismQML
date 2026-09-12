// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import "../../utils/_internal"
import "_internal" as TooltipInternal
import QtQuick.Window  // After library import: native Window type stays unshadowed 置于库import后:原生Window名归库后不被覆盖
import QtQuick  // After library import: unprefixed native types stay unshadowed 置于库import后:去前缀后保原生类型不被库覆盖

// TipPopup - Unified tip popup component 统一的提示弹出组件
// Integrates Flyout and TeachingTip, distinguished by tipType 整合 Flyout 和 TeachingTip 功能，通过 tipType 区分
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var target: null  // ✅ 2026-05-15: Item → var (鸭子类型,支持 QQuickWindow)
    property string title: ""
    property string content: ""
    property string icon: ""
    property bool closable: true
    property int duration: Enums.duration.persistent
    property bool deleteOnClose: false
    property bool modal: true
    property int tipType: Enums.tip.type_flyout
    property int animationType: Enums.flyout.pullUp
    property int anchorPosition: Enums.teachingTip.anchor_bottom
    property string primaryButtonText: ""
    property string secondaryButtonText: ""
    property bool closeOnAction: true
    // Caller content is written as ordinary declarative children; the staging Item
    // owns them visually and TipContentMover reparents them into the native surface.
    // 调用方内容按普通声明式子项书写:视觉父对象是暂存 Item,由 TipContentMover 挂进弹层。
    default property alias contentData: contentStaging.data
    readonly property int _tipRadius: Enums.surfaceRadius(Enums.radius.large)
    readonly property color _tipBackground: Enums.isVintageTicket
        ? Enums.cardColor
        : (Enums.isNeumorphism
           ? Enums.cardColor
           : (Enums.isDark ? Enums.themeColors.tooltipBgDark : Enums.themeColors.tooltipBgLight))
    readonly property real _tipBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color _tipBorderColor: Enums.isVintageTicket
        ? Enums.borderColor : Enums.stateColor.maskLight
    
    // ==================== Internal Props 内部属性 ====================
    property real _animX: 0
    property real _animY: 0
    property bool _isOpen: false
    property bool _prewarmed: false
    property bool _nativeShadowEnabled: false
    property bool _popupWindowRequested: false
    property bool _arrowWindowRequested: false
    readonly property bool _hasActions: primaryButtonText !== "" || secondaryButtonText !== ""
    readonly property var _popupWindow: popupWindowLoader.item
    readonly property var _arrowWindow: arrowWindowLoader.item
    readonly property int _prewarmCoordinate: -32000

    // Follow target control position (sync move on scroll) 跟随目标控件位置变化
    readonly property var _targetWindow: target && target.contentItem !== undefined
                                         ? target : (target ? target.Window.window : null)

    // ==================== Signals 信号 ====================
    signal closed()
    signal primaryActionTriggered()
    signal secondaryActionTriggered()

    // ==================== Public Methods 公开方法 ====================
    function show() {
        if (!target || !_ensureWindows()) return

        var popupWindow = _popupWindow
        var arrowWindow = _arrowWindow

        showAnim.stop(); hideAnim.stop(); autoCloseTimer.stop()
        _setNativeShadow(false)
        popupWindow.opacity = 0
        if (arrowWindow) arrowWindow.opacity = 0
        _isOpen = true

        var pos = posHelper.calculatePosition()
        var startPos = posHelper.getStartPosition(pos)
        _animX = startPos.x; _animY = startPos.y

        popupWindow.show(); popupWindow.raise(); popupWindow.requestActivate()
        _prewarmed = true

        if (posHelper.hasArrow && arrowWindow) {
            var arrowPos = posHelper.calculateArrowPosition(pos)
            arrowWindow.showAt(arrowPos)
        }

        if (posHelper.isHorizontalAnimation()) {
            slideXAnim.from = startPos.x; slideXAnim.to = pos.x
            slideYAnim.from = pos.y; slideYAnim.to = pos.y
            _animY = pos.y
        } else {
            slideYAnim.from = startPos.y; slideYAnim.to = pos.y
            slideXAnim.from = pos.x; slideXAnim.to = pos.x
            _animX = pos.x
        }

        showAnim.start()
        if (duration > 0) autoCloseTimer.start()
    }

    function prewarm() {
        if (!target || (_prewarmed && (!posHelper.hasArrow || _arrowWindow))) return
        if (!_ensureWindows()) return
        _prewarmWindow(_popupWindow)
        if (_arrowWindow) _prewarmWindow(_arrowWindow)
        _prewarmed = true
    }

    function close() {
        autoCloseTimer.stop()
        if (!_isOpen || !_popupWindow) return
        hideAnim.start()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _setNativeShadow(enabled) {
        if (!_popupWindow || typeof ShadowManager === "undefined" || !ShadowManager
                || _nativeShadowEnabled === enabled) return
        var applied = enabled
            ? ShadowManager.enableShadowForWindow(_popupWindow)
            : ShadowManager.disableShadowForWindow(_popupWindow)
        if (applied) _nativeShadowEnabled = enabled
    }
    function _prewarmWindow(window) {
        var savedX = window.x
        var savedY = window.y
        var savedOpacity = window.opacity
        window.x = _prewarmCoordinate
        window.y = _prewarmCoordinate
        window.opacity = 0
        window.show()
        window.hide()
        window.x = savedX
        window.y = savedY
        window.opacity = savedOpacity
    }

    function _ensureWindows() {
        _popupWindowRequested = true
        if (posHelper.hasArrow) _arrowWindowRequested = true
        if (!_popupWindow || (posHelper.hasArrow && !_arrowWindow)) {
            console.warn("TipPopup failed to create its native window surface")
            return false
        }
        contentMover.moveContent()
        return true
    }

    function _doClose() {
        _isOpen = false
        _setNativeShadow(false)
        if (_popupWindow) _popupWindow.hide()
        if (_arrowWindow) _arrowWindow.hide()
        closed()
        if (deleteOnClose) control.destroy()
    }

    function _applyTrackedPosition() {
        var pos = posHelper.calculatePosition()
        _animX = pos.x
        _animY = pos.y

        if (posHelper.hasArrow && _arrowWindow) {
            var arrowPos = posHelper.calculateArrowPosition(pos)
            _arrowWindow.x = arrowPos.x
            _arrowWindow.y = arrowPos.y
        }
    }

    function _triggerPrimaryAction() {
        primaryActionTriggered()
        if (closeOnAction) close()
    }

    function _triggerSecondaryAction() {
        secondaryActionTriggered()
        if (closeOnAction) close()
    }

    visible: false
    // Runtime-created direct children are moved when the native surface exists.
    // 原生弹层存在后,运行时直接添加的子项也会被搬迁。
    onChildrenChanged: contentMover.moveContent()

    // ==================== Content 内容 ====================
    // Staging Item for caller content; TipContentMover moves its children into the
    // native surface. A TipPopup is an invisible Item, so content cannot render here.
    // 调用方内容的暂存 Item;由 TipContentMover 把子项搬进原生弹层。TipPopup 是不可见
    // 的 Item,内容无法在这里渲染。
    Item {
        id: contentStaging
        // Content added after show() is moved over as soon as it appears.
        // show() 之后再添加的内容,出现时立刻搬迁。
        onChildrenChanged: contentMover.moveContent()
    }

    TooltipInternal.TipContentMover {
        id: contentMover
        control: control
        staging: contentStaging
        surface: control._popupWindow
        internalItems: [contentStaging, popupWindowLoader, arrowWindowLoader, positionTracker]
    }

    TooltipInternal.TipPositionHelper {
        id: posHelper
        target: control.target
        tipType: control.tipType
        animationType: control.animationType
        anchorPosition: control.anchorPosition
        viewWidth: control._hasActions ? Enums.controlSize.teachingTipWidth : 220
        viewHeight: control._hasActions ? Enums.controlSize.teachingTipHeight : 90
    }

    // Main window 主窗口
    Loader {
        id: popupWindowLoader
        active: control._popupWindowRequested
        asynchronous: false

        sourceComponent: Component {
            TooltipInternal.TipPopupWindow {
                popupControl: control
                positionHelper: posHelper
            }
        }
    }
    
    // Create the arrow window only after TeachingTip first use, then reuse it.
    // 仅在 TeachingTip 首次使用后创建箭头窗口，随后复用。
    Loader {
        id: arrowWindowLoader
        active: control._arrowWindowRequested
        asynchronous: false

        sourceComponent: Component {
            Window {
                id: arrowWindow

                function showAt(position) {
                    x = position.x
                    y = position.y
                    show()
                    raise()
                    requestArrowPaint()
                }

                function requestArrowPaint() { arrowCanvas.requestPaint() }

                objectName: "tipArrowWindow"
                flags: Qt.Tool | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint | Qt.WindowStaysOnTopHint
                color: Enums.transparent
                width: (posHelper.isLeft || posHelper.isRight) ? (posHelper.tailSize + 28) : 44
                height: (posHelper.isTop || posHelper.isBottom) ? (posHelper.tailSize + 28) : 44
                visible: false
                opacity: 0

                Item {
                    id: arrowContainer
                    anchors.centerIn: parent
                    width: (posHelper.isLeft || posHelper.isRight) ? (posHelper.tailSize + 4) : 20
                    height: (posHelper.isTop || posHelper.isBottom) ? (posHelper.tailSize + 4) : 20

                    TooltipInternal.TipArrowCanvas {
                        id: arrowCanvas
                        anchors.fill: parent
                        positionHelper: posHelper
                        popupControl: control
                    }
                }
            }
        }
    }

    // Animations 动画
    ParallelAnimation {
        id: showAnim
        onFinished: {
            if (control._isOpen && !hideAnim.running) control._setNativeShadow(true)
        }
        NumberAnimation { id: opacityAnim; target: control._popupWindow; property: "opacity"; from: 0; to: 1; duration: Enums.duration.tipShow; easing.type: Easing.OutQuad }
        NumberAnimation { id: slideXAnim; target: control; property: "_animX"; duration: Enums.duration.tipShow; easing.type: Easing.OutQuad }
        NumberAnimation { id: slideYAnim; target: control; property: "_animY"; duration: Enums.duration.tipShow; easing.type: Easing.OutQuad }
        NumberAnimation { id: arrowOpacityAnim; target: control._arrowWindow; property: "opacity"; from: 0; to: 1; duration: control._arrowWindow ? Enums.duration.tipArrow : Enums.duration.none; easing.type: Easing.OutQuad }
    }
    
    ParallelAnimation {
        id: hideAnim
        onFinished: control._doClose()
        NumberAnimation { target: control._popupWindow; property: "opacity"; from: 1; to: 0; duration: Enums.duration.tipHide; easing.type: Easing.OutQuad }
        NumberAnimation { target: control._arrowWindow; property: "opacity"; from: 1; to: 0; duration: control._arrowWindow ? Enums.duration.tipHide : Enums.duration.none; easing.type: Easing.OutQuad }
    }
    
    TooltipInternal.TipPopupAutoCloseTimer {
        id: autoCloseTimer

        host: control
    }
    
    PopupPositionTracker {
        id: positionTracker
        target: control.target
        targetWindow: control._targetWindow
        trackingEnabled: control._isOpen && !hideAnim.running
        positionEpsilon: Enums.popupMetrics.positionEpsilon
        onTargetMoved: control._applyTrackedPosition()
        onTargetOutOfView: control.close()
    }

    Connections {
        function onIsDarkChanged() {
            if (control._arrowWindow) control._arrowWindow.requestArrowPaint()
        }
        target: Enums
    }

    Connections {
        function onHoveredChanged() {
            if (control.target && control.target.hovered) control.prewarm()
        }
        function onContainsMouseChanged() {
            if (control.target && control.target.containsMouse) control.prewarm()
        }
        function onActiveFocusChanged() {
            if (control.target && control.target.activeFocus) control.prewarm()
        }

        target: control.target
        ignoreUnknownSignals: true
    }
}
