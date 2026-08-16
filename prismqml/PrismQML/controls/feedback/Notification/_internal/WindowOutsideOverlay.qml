// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../../.."
import QtQuick.Window
import QtQuick
import ".."
import "." as NotificationInternal

// WindowOutsideOverlay - Exact native host for one outside notification
// WindowOutsideOverlay - 单条窗口外通知的精确原生承载窗口
Window {
    id: control

    // ==================== Required Props 必需属性 ====================
    required property var hostWindow

    // ==================== Public Props 公开属性 ====================
    property int position: Enums.notification.posTopLeft
    property real stackOffset: 0
    property Item notificationItem: null
    property alias animator: animator
    property alias content: container

    // ==================== Readonly State 只读状态 ====================
    readonly property real contentWidth: notificationItem
        ? (notificationItem.implicitWidth > 0
            ? notificationItem.implicitWidth : notificationItem.width)
        : Enums.controlSize.toastWidth
    readonly property real contentHeight: notificationItem
        ? (notificationItem.implicitHeight > 0
            ? notificationItem.implicitHeight : notificationItem.height)
        : Enums.controlSize.toastHeight
    readonly property real _contentInset: Enums.spacing.xs / 2
    readonly property real _stackTopInset: _notificationStackInset("_stackTopInset")
    readonly property real _stackBottomInset: _notificationStackInset("_stackBottomInset")
    // ==================== Internal Props 内部属性 ====================
    property bool _closed: false
    property bool _attached: false

    // ==================== Signals 信号 ====================
    signal closed()

    // ==================== Public Methods 公开方法 ====================
    function show() {
        if (!Enums.notification.isWindowOutsidePosition(position)) {
            console.warn("WindowOutsideOverlay: posCenter has no outside edge")
            return
        }
        if (!_syncAttachment()) return
        animator.show()
    }

    function hide() {
        if (_closed) return
        animator.hide()
    }

    function updatePosition() {
        if (!_syncAttachment()) return
        animator.updatePosition()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _notificationStackInset(propertyName) {
        if (!notificationItem) return 0
        var inset = notificationItem[propertyName]
        return inset === undefined || inset === null ? 0 : _contentInset + inset
    }

    function _syncAttachment() {
        if (!hostWindow || typeof WindowHelper === "undefined" || !WindowHelper)
            return false
        var registered = WindowHelper.registerWindowAttachment(
            hostWindow,
            control,
            position,
            width,
            height,
            Enums.notification.layout.windowOutsideGap,
            stackOffset
        )
        if (registered) _attached = true
        return registered
    }

    function _releaseAttachment() {
        if (!_attached) return false
        _attached = false
        if (typeof WindowHelper !== "undefined" && WindowHelper)
            return WindowHelper.unregisterWindowAttachment(control)
        return false
    }

    function _finishClose() {
        if (_closed) return
        _closed = true
        _releaseAttachment()
        visible = false
        closed()
    }

    // ==================== Size 尺寸 ====================
    objectName: "windowOutsideNotificationOverlay"
    flags: Qt.FramelessWindowHint | Qt.Tool
    visible: false
    color: Enums.transparent
    width: contentWidth + _contentInset * 2
    height: contentHeight + _contentInset * 2
    transientParent: null

    onWidthChanged: {
        if (visible && !animator._hiding) updatePosition()
    }
    onHeightChanged: {
        if (visible && !animator._hiding) updatePosition()
    }
    onStackOffsetChanged: {
        if (visible && !animator._hiding) updatePosition()
    }
    onClosing: (close) => control._finishClose()
    Component.onDestruction: {
        _releaseAttachment()
    }

    // ==================== Content 内容 ====================
    NotificationInternal.WindowOutsideGeometry {
        id: outsideGeometry

        hostWindow: control.hostWindow
        position: control.position
        targetWidth: control.width
        targetHeight: control.height
        stackOffset: control.stackOffset
    }

    NotificationAnimator {
        id: animator

        target: control
        position: control.position
        parentItem: outsideGeometry
        stackOffset: control.stackOffset
        onHideFinished: control._finishClose()
    }

    Item {
        id: container

        anchors.fill: parent
    }

    Connections {
        function onXChanged() { if (control.visible) control.updatePosition() }
        function onYChanged() { if (control.visible) control.updatePosition() }
        function onWidthChanged() { if (control.visible) control.updatePosition() }
        function onHeightChanged() { if (control.visible) control.updatePosition() }
        function onClosing(close) { control._finishClose() }
        function onVisibleChanged() {
            if (control.hostWindow && !control.hostWindow.visible)
                control._finishClose()
        }
        function onVisibilityChanged() {
            if (!control.hostWindow) return
            if (control.hostWindow.visibility === Window.Hidden
                    || control.hostWindow.visibility === Window.Minimized)
                control._finishClose()
        }

        target: control.hostWindow
        ignoreUnknownSignals: true
    }

    Connections {
        function onWindowFollowerReservationsChanged() {
            if (control.visible) control.updatePosition()
        }

        target: typeof WindowHelper !== "undefined" ? WindowHelper : null
        ignoreUnknownSignals: true
    }
}
