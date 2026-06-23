// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick.Effects
import "../../.."
import "../../buttons"
import "../../data/Label"
import "_internal"
import QtQuick.Window  // 置于库import后:原生Window名归库后不被覆盖
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// TipPopup - Unified tip popup component 统一的提示弹出组件
// Integrates Flyout and TeachingTip, distinguished by tipType 整合 Flyout 和 TeachingTip 功能，通过 tipType 区分
Item {
    id: control
    visible: false
    
    // ==================== Public Properties 公共属性 ====================
    property var target: null  // ✅ 2026-05-15: Item → var (鸭子类型,支持 QQuickWindow)
    property string title: ""
    property string content: ""
    property string icon: ""
    property bool closable: true
    property int duration: -1
    property bool deleteOnClose: false
    property bool modal: true
    property int tipType: Enums.tip.type_flyout
    property int animationType: Enums.flyout.pullUp
    property int anchorPosition: Enums.teachingTip.anchor_bottom
    
    signal closed()

    // ==================== Internal State 内部状态 ====================
    property real _animX: 0
    property real _animY: 0
    property bool _isOpen: false

    // Follow target control position (sync move on scroll) 跟随目标控件位置变化
    property point _lastTargetGlobalPos: Qt.point(-1, -1)

    // ==================== Methods 方法 ====================
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

    function _doClose() {
        _isOpen = false
        popupWindow.hide(); arrowWindow.hide()
        closed()
        if (deleteOnClose) control.destroy()
    }

    // ==================== Position Helper 位置助手 ====================
    TipPositionHelper {
        id: posHelper
        target: control.target
        tipType: control.tipType
        animationType: control.animationType
        anchorPosition: control.anchorPosition
        viewWidth: 220
        viewHeight: 90
    }

    // ==================== Main Window 主窗口 ====================
    Window {
        id: popupWindow
        flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
        color: Enums.transparent
        width: posHelper.viewWidth
        height: posHelper.viewHeight
        x: _animX
        y: _animY
        
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
            radius: Enums.radius.large
            color: Enums.isDark ? Enums.themeColors.tooltipBgDark : Enums.themeColors.tooltipBgLight
            border.width: Enums.border.thin
            border.color: Enums.stateColor.maskLight
            
            Column {
                anchors.fill: parent
                anchors.margins: Enums.spacing.l
                anchors.rightMargin: control.closable ? 32 : Enums.spacing.l
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
            
            CloseButton {
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.topMargin: Enums.spacing.xs
                anchors.rightMargin: Enums.spacing.xs
                visible: control.closable
                onClicked: control.close()
            }
        }
        opacity: 0
    }
    
    // ==================== Arrow Window 箭头窗口 ====================
    Window {
        id: arrowWindow
        flags: Qt.Tool | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint | Qt.WindowStaysOnTopHint
        color: Enums.transparent
        width: (posHelper.isLeft || posHelper.isRight) ? (posHelper.tailSize + 28) : 44
        height: (posHelper.isTop || posHelper.isBottom) ? (posHelper.tailSize + 28) : 44
        visible: false
        
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
                    var bgColor = Enums.isDark ? Enums.themeColors.tooltipBgDark : Enums.themeColors.tooltipBgLight
                    var borderColor = Enums.stateColor.maskLight
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
        opacity: 0
    }

    // ==================== Animations 动画 ====================
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
    
    // ==================== Position Tracker 位置跟踪 ====================
    Timer {
        id: positionTracker
        interval: Enums.popupMetrics.trackerIntervalMs
        repeat: true
        running: control._isOpen && control.target !== null
        onTriggered: {
            if (!control.target) return
            
            // Get current global position of target control 获取目标控件当前全局位置
            var currentGlobalPos = control.target.mapToGlobal(0, 0)
            
            // Skip if position unchanged (most common case) 位置未变则跳过
            if (Math.abs(currentGlobalPos.x - control._lastTargetGlobalPos.x) < Enums.popupMetrics.positionEpsilon &&
                Math.abs(currentGlobalPos.y - control._lastTargetGlobalPos.y) < Enums.popupMetrics.positionEpsilon) {
                return
            }
            control._lastTargetGlobalPos = currentGlobalPos
            
            // Check if target is in main window visible area 检查是否在可视区域
            var mainWindow = control.target.Window.window
            if (mainWindow) {
                var localPos = control.target.mapToItem(mainWindow.contentItem, 0, 0)
                // Close popup if target scrolled out of view 滚动出视区则关闭
                if (localPos.y < -control.target.height || localPos.y > mainWindow.height ||
                    localPos.x < -control.target.width || localPos.x > mainWindow.width) {
                    control.close()
                    return
                }
            }
            
            // Update position 更新位置
            var pos = posHelper.calculatePosition()
            control._animX = pos.x
            control._animY = pos.y
            
            // Update arrow position if TeachingTip 更新箭头位置
            if (posHelper.hasArrow) {
                var arrowPos = posHelper.calculateArrowPosition(pos)
                arrowWindow.x = arrowPos.x
                arrowWindow.y = arrowPos.y
            }
        }
    }

    Connections {
        target: ThemeManager
        function onThemeChanged() { arrowCanvas.requestPaint() }
    }
}
