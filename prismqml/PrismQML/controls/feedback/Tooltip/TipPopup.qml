// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick.Effects
import "../../.."
import "../../buttons"
import "../../data/Label"
import "../../utils/_internal"
import "_internal"
import QtQuick.Window  // 置于库import后:原生Window名归库后不被覆盖
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

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
    readonly property int _tipRadius: Enums.radius.large
    readonly property color _tipBackground: (Enums.isDark ? Enums.themeColors.tooltipBgDark : Enums.themeColors.tooltipBgLight)
    readonly property int _tipBorderWidth: Enums.border.thin
    readonly property color _tipBorderColor: Enums.stateColor.maskLight
    
    // ==================== Internal Props 内部属性 ====================
    property real _animX: 0
    property real _animY: 0
    property bool _isOpen: false
    readonly property bool _hasActions: primaryButtonText !== "" || secondaryButtonText !== ""

    // Follow target control position (sync move on scroll) 跟随目标控件位置变化
    readonly property var _targetWindow: target && target.contentItem !== undefined
                                         ? target : (target ? target.Window.window : null)

    // ==================== Signals 信号 ====================
    signal closed()
    signal primaryActionTriggered()
    signal secondaryActionTriggered()

    // ==================== Public Methods 公开方法 ====================
    function show() {
        if (!target) return

        showAnim.stop(); hideAnim.stop(); autoCloseTimer.stop()
        popupWindow.opacity = 0; arrowWindow.opacity = 0
        _isOpen = true

        var pos = posHelper.calculatePosition()
        var startPos = posHelper.getStartPosition(pos)
        _animX = startPos.x; _animY = startPos.y

        popupWindow.show(); popupWindow.raise(); popupWindow.requestActivate()

        Qt.callLater(function() {
            if (ShadowManager) ShadowManager.enableShadowForWindow(popupWindow)
        })

        if (posHelper.hasArrow) {
            var arrowPos = posHelper.calculateArrowPosition(pos)
            arrowWindow.x = arrowPos.x; arrowWindow.y = arrowPos.y
            arrowWindow.show(); arrowWindow.raise()
            arrowCanvas.requestPaint()
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

    function close() {
        autoCloseTimer.stop()
        hideAnim.start()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _doClose() {
        _isOpen = false
        popupWindow.hide(); arrowWindow.hide()
        closed()
        if (deleteOnClose) control.destroy()
    }

    function _applyTrackedPosition() {
        var pos = posHelper.calculatePosition()
        _animX = pos.x
        _animY = pos.y

        if (posHelper.hasArrow) {
            var arrowPos = posHelper.calculateArrowPosition(pos)
            arrowWindow.x = arrowPos.x
            arrowWindow.y = arrowPos.y
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

    // ==================== Content 内容 ====================
    TipPositionHelper {
        id: posHelper
        target: control.target
        tipType: control.tipType
        animationType: control.animationType
        anchorPosition: control.anchorPosition
        viewWidth: control._hasActions ? Enums.controlSize.teachingTipWidth : 220
        viewHeight: control._hasActions ? Enums.controlSize.teachingTipHeight : 90
    }

    // Main window 主窗口
    Window {
        id: popupWindow
        flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
        color: Enums.transparent
        width: posHelper.viewWidth
        height: posHelper.viewHeight
        x: _animX
        y: _animY
        opacity: 0
        
        // Focus detection for click outside close 焦点检测实现点击外部关闭
        onActiveFocusItemChanged: {
            if (!activeFocusItem && control._isOpen && control.modal) {
                Qt.callLater(function() {
                    if (!popupWindow.activeFocusItem && control._isOpen) {
                        control.close()
                    }
                })
            }
        }
        
        Rectangle {
            id: contentRect
            anchors.fill: parent
            radius: control._tipRadius
            color: control._tipBackground
            border.width: control._tipBorderWidth
            border.color: control._tipBorderColor
            
            Column {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: actionRow.visible ? actionRow.top : parent.bottom
                anchors.topMargin: Enums.spacing.l
                anchors.leftMargin: Enums.spacing.l
                anchors.rightMargin: control.closable ? 32 : Enums.spacing.l
                anchors.bottomMargin: actionRow.visible ? Enums.spacing.s : Enums.spacing.l
                spacing: Enums.spacing.xs
                
                Label {
                    type: Enums.label.type_body_strong
                    text: control.title
                    visible: text !== ""
                }
                
                Label {
                    type: Enums.label.type_caption
                    text: control.content
                    color: Enums.textColor.secondary
                    wrapMode: Text.Wrap
                    width: parent.width
                    visible: text !== ""
                }
            }

            // Create action controls only for tips that expose actions.
            // 仅为带操作的提示创建操作控件。
            Loader {
                id: actionRow

                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.rightMargin: Enums.spacing.l
                anchors.bottomMargin: Enums.spacing.l
                active: control._hasActions
                visible: active
                sourceComponent: Row {
                    spacing: Enums.spacing.m

                    Button {
                        objectName: "tipSecondaryActionButton"
                        text: control.secondaryButtonText
                        visible: text !== ""
                        onClicked: control._triggerSecondaryAction()
                    }

                    Button {
                        objectName: "tipPrimaryActionButton"
                        style: Enums.button.style_primary
                        text: control.primaryButtonText
                        visible: text !== ""
                        onClicked: control._triggerPrimaryAction()
                    }
                }
            }
            
            CloseButton {
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.topMargin: Enums.spacing.xs
                anchors.rightMargin: Enums.spacing.xs
                visible: control.closable
                onClicked: control.close()
            }
        }
    }
    
    // Arrow window 箭头窗口
    Window {
        id: arrowWindow
        flags: Qt.Tool | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint | Qt.WindowStaysOnTopHint
        color: Enums.transparent
        width: (posHelper.isLeft || posHelper.isRight) ? (posHelper.tailSize + 28) : 44
        height: (posHelper.isTop || posHelper.isBottom) ? (posHelper.tailSize + 28) : 44
        visible: false
        opacity: 0
        
        Component.onCompleted: {
            if (posHelper.isTeachingTip) {
                arrowWindow.show()
                arrowWindow.hide()
            }
        }
        
        Item {
            id: arrowContainer
            anchors.centerIn: parent
            width: (posHelper.isLeft || posHelper.isRight) ? (posHelper.tailSize + 4) : 20
            height: (posHelper.isTop || posHelper.isBottom) ? (posHelper.tailSize + 4) : 20
            
            Canvas {
                id: arrowCanvas
                anchors.fill: parent
                
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.reset()
                    var bgColor = control._tipBackground
                    var borderColor = control._tipBorderColor
                    var w = width, h = height, inset = 2
                    
                    // Draw filled triangle 绘制填充三角形
                    ctx.beginPath()
                    if (posHelper.isBottom) {
                        ctx.moveTo(inset, inset)
                        ctx.lineTo(w/2, h - inset)
                        ctx.lineTo(w - inset, inset)
                    } else if (posHelper.isTop) {
                        ctx.moveTo(inset, h - inset)
                        ctx.lineTo(w/2, inset)
                        ctx.lineTo(w - inset, h - inset)
                    } else if (posHelper.isLeft) {
                        ctx.moveTo(w - inset, inset)
                        ctx.lineTo(inset, h/2)
                        ctx.lineTo(w - inset, h - inset)
                    } else if (posHelper.isRight) {
                        ctx.moveTo(inset, inset)
                        ctx.lineTo(w - inset, h/2)
                        ctx.lineTo(inset, h - inset)
                    }
                    ctx.closePath()
                    ctx.fillStyle = bgColor
                    ctx.fill()
                    
                    // Draw border on two sides only (not the edge touching main window) 只描两条斜边（不描贴着主窗口的那条边）

                    ctx.beginPath()
                    ctx.strokeStyle = borderColor
                    ctx.lineWidth = Enums.border.thin
                    if (posHelper.isBottom) {
                        ctx.moveTo(inset, inset)
                        ctx.lineTo(w/2, h - inset)
                        ctx.lineTo(w - inset, inset)
                    } else if (posHelper.isTop) {
                        ctx.moveTo(inset, h - inset)
                        ctx.lineTo(w/2, inset)
                        ctx.lineTo(w - inset, h - inset)
                    } else if (posHelper.isLeft) {
                        ctx.moveTo(w - inset, inset)
                        ctx.lineTo(inset, h/2)
                        ctx.lineTo(w - inset, h - inset)
                    } else if (posHelper.isRight) {
                        ctx.moveTo(inset, inset)
                        ctx.lineTo(w - inset, h/2)
                        ctx.lineTo(inset, h - inset)
                    }
                    ctx.stroke()
                }
            }
        }
    }

    // Animations 动画
    ParallelAnimation {
        id: showAnim
        NumberAnimation { id: opacityAnim; target: popupWindow; property: "opacity"; from: 0; to: 1; duration: Enums.duration.tipShow; easing.type: Easing.OutQuad }
        NumberAnimation { id: slideXAnim; target: control; property: "_animX"; duration: Enums.duration.tipShow; easing.type: Easing.OutQuad }
        NumberAnimation { id: slideYAnim; target: control; property: "_animY"; duration: Enums.duration.tipShow; easing.type: Easing.OutQuad }
        NumberAnimation { id: arrowOpacityAnim; target: arrowWindow; property: "opacity"; from: 0; to: 1; duration: Enums.duration.tipArrow; easing.type: Easing.OutQuad }
    }
    
    ParallelAnimation {
        id: hideAnim
        onFinished: control._doClose()
        NumberAnimation { target: popupWindow; property: "opacity"; from: 1; to: 0; duration: Enums.duration.tipHide; easing.type: Easing.OutQuad }
        NumberAnimation { target: arrowWindow; property: "opacity"; from: 1; to: 0; duration: Enums.duration.tipHide; easing.type: Easing.OutQuad }
    }
    
    Timer {
        id: autoCloseTimer
        interval: control.duration
        onTriggered: control.close()
    }
    
    PopupPositionTracker {
        target: control.target
        targetWindow: control._targetWindow
        trackingEnabled: control._isOpen && !hideAnim.running
        positionEpsilon: Enums.popupMetrics.positionEpsilon
        onTargetMoved: control._applyTrackedPosition()
        onTargetOutOfView: control.close()
    }

    Connections {
        function onIsDarkChanged() { arrowCanvas.requestPaint() }
        target: Enums
    }
}
