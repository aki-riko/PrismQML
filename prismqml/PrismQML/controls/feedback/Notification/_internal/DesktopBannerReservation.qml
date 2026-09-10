// DesktopBannerReservation - Banner avoidance reservation for desktop notifications 桌面通知的横幅避让保留量
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// Windows notification banners live in a higher window band (4) than any ordinary topmost
// window (1) and cannot be covered, so edge-anchored desktop notifications reserve the
// space those banners occupy at the same screen edge.
// Windows通知横幅位于比普通topmost窗口更高的窗口层带(4)且无法被压过，
// 因此贴边锚定的桌面通知会保留横幅在同一屏幕边缘占用的空间。
QtObject {
    id: control

    // ==================== Required Props 必需属性 ====================
    // Host notification window exposing `screen`, `visible` and `position`.
    // 宿主通知窗口，需暴露 `screen`、`visible` 与 `position`。
    required property var targetWindow

    // ==================== Internal Props 内部属性 ====================
    // Resolved through the QML context so bare QML hosts without the injected guard still work.
    // 通过QML上下文解析，使未注入守卫的裸QML宿主仍可工作。
    readonly property var guard: (typeof NotificationBannerGuard !== "undefined" && NotificationBannerGuard)
        ? NotificationBannerGuard : null
    readonly property real _ratio: {
        var target = targetWindow ? targetWindow.screen : null
        var value = target ? target.devicePixelRatio : 1
        return value > 0 ? value : 1
    }
    readonly property int _position: {
        if (!targetWindow || targetWindow.position === undefined) return Enums.notification.posBottomRight
        return targetWindow.position
    }
    // Reserved space in logical pixels 保留空间（逻辑像素）
    readonly property real bottomInset: _insetFor(guard ? guard.bottomReservedHeight : 0)
    readonly property real topInset: _insetFor(guard ? guard.topReservedHeight : 0)
    // Reservation for the edge the host is anchored to 宿主锚定边缘对应的保留量
    readonly property real inset: Enums.notification.isBottom(_position)
        ? bottomInset
        : (Enums.notification.isTop(_position) ? topInset : 0)
    property bool _watching: false
    property Connections _guardConnections: Connections {
        function onReservationsChanged() {
            control.reservationsChanged()
            control._repositionHost()
        }

        target: control.guard
        ignoreUnknownSignals: true
    }
    // Watch automatically while the host window is visible 宿主窗口可见期间自动监视
    property Connections _visibilityConnections: Connections {
        function onVisibleChanged() { control._syncWatch() }

        target: control.targetWindow
        ignoreUnknownSignals: true
    }

    // ==================== Signals 信号 ====================
    signal reservationsChanged()

    // ==================== Public Methods 公开方法 ====================
    function acquire() {
        if (_watching || !guard) return
        _watching = true
        guard.acquire()
    }

    function release() {
        if (!_watching || !guard) return
        _watching = false
        guard.release()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _syncWatch() {
        if (targetWindow && targetWindow.visible === true) acquire()
        else release()
    }

    // Re-anchor the host so a changed reservation actually moves the notification.
    // 重新锚定宿主，使变化后的保留量真正移动通知。
    function _repositionHost() {
        if (!targetWindow) return
        if (typeof targetWindow.updatePosition === "function") {
            targetWindow.updatePosition()
            return
        }
        var animator = targetWindow.animator
        if (animator && typeof animator.updatePosition === "function") {
            animator.updatePosition()
        }
    }

    // Convert one physical reservation to logical pixels and drop the transparent margin
    // the banner window keeps above its visual card.
    // 将物理保留高度换算为逻辑像素，并扣除横幅窗口在卡片上方的透明边距。
    function _insetFor(physicalHeight) {
        if (!physicalHeight || physicalHeight <= 0) return 0
        var occupied = physicalHeight / _ratio
            - Enums.notification.layout.bannerWindowInset
        return occupied > 0 ? occupied + Enums.notification.layout.bannerGap : 0
    }

    Component.onCompleted: _syncWatch()
    Component.onDestruction: release()
}
