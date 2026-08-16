// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import "../../.."
import "_internal" as NotificationInternal

// NotificationAnimator - Shared slide animation for notifications 通知滑动动画共享组件
// Used by Toast, InfoBar and desktop windows 供Toast、InfoBar和桌面窗口使用
// Supports both window-relative and available-screen positioning 支持窗口相对定位和屏幕可用工作区定位
QtObject {
    id: animator

    // ==================== Required Props 必需属性 ====================
    required property var target         // Target item/window to animate 动画目标（Item或Window）
    required property int position       // Nine-grid position enum (0-8) 九宫格位置枚举

    // ==================== Public Props 公开属性 ====================
    property var parentItem: null        // Parent for position calculation (window mode) 用于位置计算的父容器（窗口模式）
    property bool desktopMode: false     // Use screen coordinates instead of parent 使用屏幕坐标而非父容器
    property int showDuration: Enums.notification.animation.showDuration
    property int hideDuration: Enums.notification.animation.hideDuration
    property real stackOffset: 0         // Stack offset for multiple notifications 多通知堆叠偏移

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isTop: Enums.notification.isTop(position)
    readonly property bool _isMiddle: Enums.notification.isMiddle(position)
    readonly property bool _isBottom: Enums.notification.isBottom(position)
    readonly property bool _isLeft: Enums.notification.isLeft(position)
    readonly property bool _isRight: Enums.notification.isRight(position)
    readonly property bool _isHorizontalCenter: Enums.notification.isHorizontalCenter(position)
    readonly property real _targetWidth: target ? target.width : 0
    readonly property real _targetHeight: target ? target.height : 0
    readonly property real _slideOffset: _targetWidth + Enums.notification.layout.edgeMargin
    readonly property real _slideOffsetY: _targetHeight + Enums.notification.layout.verticalSlideExtra
    readonly property int _showEasing: Enums.notification.animation.showEasing
    readonly property real _showOvershoot: Enums.notification.animation.showOvershoot
    readonly property int _hideEasing: Enums.notification.animation.hideEasing

    // ==================== Internal Props 内部属性 ====================
    property real _baseX: 0
    property real _baseY: 0
    property bool _positioned: false
    property bool _hiding: false
    property ParallelAnimation _showAnim: ParallelAnimation {
        onFinished: animator.showFinished()

        NumberAnimation {
            target: animator.target
            property: "x"
            to: animator._baseX
            duration: animator.showDuration
            easing.type: animator._showEasing
            easing.overshoot: animator._showOvershoot
        }
        NumberAnimation {
            target: animator.target
            property: "y"
            to: animator._baseY
            duration: animator.showDuration
            easing.type: animator._showEasing
            easing.overshoot: animator._showOvershoot
        }
    }
    property ParallelAnimation _hideAnim: ParallelAnimation {
        onFinished: {
            animator._positioned = false
            animator._hiding = false
            animator.hideFinished()
        }

        NumberAnimation {
            target: animator.target
            property: "x"
            to: animator._isLeft ? animator._baseX - animator._slideOffset
                : (animator._isRight ? animator._baseX + animator._slideOffset : animator._baseX)
            duration: animator.hideDuration
            easing.type: animator._hideEasing
        }
        NumberAnimation {
            target: animator.target
            property: "y"
            to: animator._isHorizontalCenter && animator._isTop
                ? animator._baseY - animator._slideOffsetY
                : (animator._isHorizontalCenter && animator._isBottom
                    ? animator._baseY + animator._slideOffsetY : animator._baseY)
            duration: animator.hideDuration
            easing.type: animator._hideEasing
        }
        NumberAnimation {
            target: animator.target
            property: "opacity"
            to: animator._isMiddle && animator._isHorizontalCenter ? 0 : 1
            duration: animator.hideDuration
            easing.type: animator._hideEasing
        }
    }
    property ParallelAnimation _repositionAnim: ParallelAnimation {
        NumberAnimation {
            target: animator.target
            property: "x"
            to: animator._baseX
            duration: Enums.notification.animation.repositionDuration
            easing.type: Enums.notification.animation.repositionEasing
        }
        NumberAnimation {
            target: animator.target
            property: "y"
            to: animator._baseY
            duration: Enums.notification.animation.repositionDuration
            easing.type: Enums.notification.animation.repositionEasing
        }
    }
    property Timer _geometryUpdateTimer: NotificationInternal.NotificationAnimatorGeometryUpdateTimer {
        host: animator
    }
    property Connections _targetConnections: Connections {
        function onWidthChanged() { animator._schedulePositionUpdate() }
        function onHeightChanged() { animator._schedulePositionUpdate() }
        function onScreenChanged() { animator._schedulePositionUpdate() }

        target: animator.target
        ignoreUnknownSignals: true
    }
    property Connections _parentConnections: Connections {
        function onWidthChanged() { animator._schedulePositionUpdate() }
        function onHeightChanged() { animator._schedulePositionUpdate() }

        target: animator.parentItem
        ignoreUnknownSignals: true
    }
    property Connections _screenConnections: Connections {
        function onDesktopGeometryChanged() { animator._schedulePositionUpdate() }
        function onWidthChanged() { animator._schedulePositionUpdate() }
        function onHeightChanged() { animator._schedulePositionUpdate() }
        function onVirtualXChanged() { animator._schedulePositionUpdate() }
        function onVirtualYChanged() { animator._schedulePositionUpdate() }

        target: animator.desktopMode && animator.target ? animator.target.screen : null
        ignoreUnknownSignals: true
    }

    // ==================== Signals 信号 ====================
    signal showFinished()
    signal hideFinished()

    // ==================== Internal Methods 内部方法 ====================
    function _desktopAvailableGeometry() {
        var screenInfo = target && target.screen ? target.screen : Screen
        var virtualX = screenInfo.virtualX
        var virtualY = screenInfo.virtualY
        var screenWidth = screenInfo.width
        var screenHeight = screenInfo.height

        if (typeof WindowHelper !== "undefined" && WindowHelper
                && typeof WindowHelper.availableScreenGeometryAt === "function") {
            var geometry = WindowHelper.availableScreenGeometryAt(
                virtualX + Math.floor(screenWidth / 2),
                virtualY + Math.floor(screenHeight / 2)
            )
            if (geometry && geometry.width > 0 && geometry.height > 0)
                return geometry
        }

        // QML Screen does not expose QScreen.availableGeometry. Supported hosts
        // inject WindowHelper above; this is a best-effort fallback for bare QML hosts.
        // QML Screen 不公开 QScreen.availableGeometry；受支持宿主通过上方
        // WindowHelper 注入精确工作区，裸 QML 宿主在此使用可用宽高兜底。
        return {
            "x": virtualX,
            "y": virtualY,
            "width": screenInfo.desktopAvailableWidth > 0
                ? screenInfo.desktopAvailableWidth : screenWidth,
            "height": screenInfo.desktopAvailableHeight > 0
                ? screenInfo.desktopAvailableHeight : screenHeight
        }
    }

    function _calculateBasePosition() {
        if (!target) return

        var margin = Enums.notification.layout.screenMargin
        var originX = 0
        var originY = 0
        var pw = 0
        var ph = 0

        if (desktopMode) {
            var available = _desktopAvailableGeometry()
            originX = available.x
            originY = available.y
            pw = available.width
            ph = available.height
        } else {
            if (!parentItem) return
            pw = parentItem.width
            ph = parentItem.height
        }

        if (_isLeft)
            _baseX = originX + margin
        else if (_isRight)
            _baseX = originX + pw - _targetWidth - margin
        else
            _baseX = originX + (pw - _targetWidth) / 2

        if (_isTop)
            _baseY = originY + margin + stackOffset
        else if (_isBottom)
            _baseY = originY + ph - _targetHeight - margin - stackOffset
        else
            _baseY = originY + (ph - _targetHeight) / 2 + stackOffset
    }

    function _schedulePositionUpdate() {
        if (!_positioned || _hiding || !target || !target.visible) return
        _geometryUpdateTimer.restart()
    }

    function _setStartPosition() {
        if (_isLeft) {
            target.x = _baseX - _slideOffset
            target.y = _baseY
        } else if (_isRight) {
            target.x = _baseX + _slideOffset
            target.y = _baseY
        } else {
            target.x = _baseX
            target.y = _isTop ? _baseY - _slideOffsetY
                : (_isBottom ? _baseY + _slideOffsetY : _baseY)
        }
    }

    // ==================== Public Methods 公开方法 ====================
    function show() {
        if (!target) return
        _hideAnim.stop()
        _repositionAnim.stop()
        _hiding = false
        _calculateBasePosition()
        _setStartPosition()
        _positioned = true
        target.visible = true
        if (target.opacity !== undefined) target.opacity = 1
        _showAnim.start()
    }

    function hide() {
        if (!target || _hiding) return
        _geometryUpdateTimer.stop()
        _showAnim.stop()
        _repositionAnim.stop()
        _hiding = true
        _hideAnim.start()
    }

    function updatePosition(newStackOffset) {
        if (!target) return
        if (newStackOffset !== undefined) stackOffset = newStackOffset
        _calculateBasePosition()
        if (!_positioned || _hiding || !target.visible) return
        _showAnim.stop()
        _repositionAnim.stop()
        _repositionAnim.start()
    }
}
