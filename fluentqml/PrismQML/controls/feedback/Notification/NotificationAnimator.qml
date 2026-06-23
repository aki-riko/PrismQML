// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import "../../.."

// NotificationAnimator - Shared slide animation for notifications 通知滑动动画共享组件
// Used by Toast, InfoBar and DesktopOverlay 供Toast、InfoBar和DesktopOverlay使用
// Supports both window-relative and screen-absolute positioning 支持窗口相对定位和屏幕绝对定位
// Usage 用法:
//   NotificationAnimator {
//       id: animator
//       target: control
//       position: control.position
//       parentItem: control.parent  // For window mode 窗口模式
//       desktopMode: true           // For desktop mode 桌面模式
//   }
//   Then call animator.show() / animator.hide()
QtObject {
    id: animator
    
    // ==================== Required Props 必需属性 ====================
    required property var target         // Target item/window to animate 动画目标（Item或Window）
    required property int position       // Position enum (0-5) 位置枚举
    
    // ==================== Optional Props 可选属性 ====================
    property var parentItem: null        // Parent for position calculation (window mode) 用于位置计算的父容器（窗口模式）
    property bool desktopMode: false     // Use screen coordinates instead of parent 使用屏幕坐标而非父容器
    property int showDuration: Enums.notification.animation.showDuration
    property int hideDuration: Enums.notification.animation.hideDuration
    property real stackOffset: 0  // Stack offset for multiple notifications 堆叠偏移
    
    // ==================== Signals 信号 ====================
    signal showFinished()
    signal hideFinished()
    
    // ==================== Position Helpers 位置辅助 ====================
    readonly property bool _isTop: Enums.notification.isTop(position)
    readonly property bool _isLeft: Enums.notification.isLeft(position)
    readonly property bool _isRight: Enums.notification.isRight(position)
    readonly property bool _isCenter: Enums.notification.isCenter(position)
    
    // ==================== Slide Offsets 滑动偏移 ====================
    readonly property real _targetWidth: target ? target.width : 0
    readonly property real _targetHeight: target ? target.height : 0
    readonly property real _slideOffset: _targetWidth + Enums.notification.layout.edgeMargin
    // Vertical slide needs larger offset for better bounce effect 垂直滑动需要更大偏移以获得更好的回弹效果
    readonly property real _slideOffsetY: _targetHeight + Enums.notification.layout.verticalSlideExtra
    
    // ==================== Base Position 基准位置 ====================
    property real _baseX: 0
    property real _baseY: 0
    
    function _calculateBasePosition() {
        if (!target) return
        
        var margin = Enums.notification.layout.screenMargin
        var pw, ph
        
        if (desktopMode) {
            // Desktop mode: use screen dimensions 桌面模式：使用屏幕尺寸
            pw = Screen.width
            ph = Screen.height
            var taskbarOffset = Enums.notification.layout.taskbarOffset
            // Apply stack offset based on position 根据位置应用堆叠偏移
            var stackY = _isTop ? stackOffset : -stackOffset
            
            switch (position) {
                case 0: _baseX = margin; _baseY = margin + stackY; break  // TopLeft
                case 1: _baseX = (pw - _targetWidth) / 2; _baseY = margin + stackY; break  // Top
                case 2: _baseX = pw - _targetWidth - margin; _baseY = margin + stackY; break  // TopRight
                case 3: _baseX = margin; _baseY = ph - _targetHeight - margin - taskbarOffset + stackY; break  // BottomLeft
                case 4: _baseX = (pw - _targetWidth) / 2; _baseY = ph - _targetHeight - margin - taskbarOffset + stackY; break  // Bottom
                case 5: default: _baseX = pw - _targetWidth - margin; _baseY = ph - _targetHeight - margin - taskbarOffset + stackY; break  // BottomRight
            }
        } else {
            // Window mode: use parent dimensions 窗口模式：使用父容器尺寸
            if (!parentItem) return
            pw = parentItem.width
            ph = parentItem.height
            // Apply stack offset based on position 根据位置应用堆叠偏移
            var stackYWin = _isTop ? stackOffset : -stackOffset
            
            switch (position) {
                case 0: _baseX = margin; _baseY = margin + stackYWin; break  // TopLeft
                case 1: _baseX = (pw - _targetWidth) / 2; _baseY = margin + stackYWin; break  // Top
                case 2: _baseX = pw - _targetWidth - margin; _baseY = margin + stackYWin; break  // TopRight
                case 3: _baseX = margin; _baseY = ph - _targetHeight - margin + stackYWin; break  // BottomLeft
                case 4: _baseX = (pw - _targetWidth) / 2; _baseY = ph - _targetHeight - margin + stackYWin; break  // Bottom
                case 5: default: _baseX = pw - _targetWidth - margin; _baseY = ph - _targetHeight - margin + stackYWin; break  // BottomRight
            }
        }
    }
    
    // ==================== Animation Config 动画配置 ====================
    readonly property int _showEasing: Enums.notification.animation.showEasing
    readonly property real _showOvershoot: Enums.notification.animation.showOvershoot
    readonly property int _hideEasing: Enums.notification.animation.hideEasing
    
    // ==================== Animations 动画 ====================
    property ParallelAnimation _showAnim: ParallelAnimation {
        NumberAnimation {
            target: animator.target; property: "x"; to: animator._baseX
            duration: animator.showDuration
            easing.type: animator._showEasing; easing.overshoot: animator._showOvershoot
        }
        NumberAnimation {
            target: animator.target; property: "y"; to: animator._baseY
            duration: animator.showDuration
            easing.type: animator._showEasing; easing.overshoot: animator._showOvershoot
        }
        onFinished: animator.showFinished()
    }
    
    property ParallelAnimation _hideAnim: ParallelAnimation {
        NumberAnimation {
            target: animator.target; property: "x"
            to: animator._isLeft ? animator._baseX - animator._slideOffset :
                (animator._isRight ? animator._baseX + animator._slideOffset : animator._baseX)
            duration: animator.hideDuration
            easing.type: animator._hideEasing
        }
        NumberAnimation {
            target: animator.target; property: "y"
            to: animator._isCenter ? (animator._isTop ? animator._baseY - animator._slideOffsetY : animator._baseY + animator._slideOffsetY) : animator._baseY
            duration: animator.hideDuration
            easing.type: animator._hideEasing
        }
        onFinished: animator.hideFinished()
    }
    
    // ==================== Public Methods 公开方法 ====================
    function show() {
        if (!target) return
        _hideAnim.stop()
        _calculateBasePosition()
        
        // Set initial position (from outside edge) 设置初始位置（从边缘外）
        if (_isLeft) {
            target.x = _baseX - _slideOffset
            target.y = _baseY
        } else if (_isRight) {
            target.x = _baseX + _slideOffset
            target.y = _baseY
        } else if (_isCenter) {
            target.x = _baseX
            target.y = _isTop ? _baseY - _slideOffsetY : _baseY + _slideOffsetY
        }
        
        target.visible = true
        if (target.opacity !== undefined) target.opacity = 1
        _showAnim.start()
    }
    
    function hide() {
        if (!target) return
        _showAnim.stop()
        _hideAnim.start()
    }
    
    function updatePosition(newStackOffset) {
        if (!target) return
        stackOffset = newStackOffset !== undefined ? newStackOffset : stackOffset
        _calculateBasePosition()
        // Animate to new position 动画到新位置
        _repositionAnim.start()
    }
    
    // Reposition animation for stack changes 堆叠变化时的重定位动画
    property NumberAnimation _repositionAnim: NumberAnimation {
        target: animator.target
        property: "y"
        to: animator._baseY
        duration: Enums.notification.animation.repositionDuration
        easing.type: Enums.notification.animation.repositionEasing
    }
}
