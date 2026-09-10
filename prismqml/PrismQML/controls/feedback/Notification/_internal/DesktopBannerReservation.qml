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
    // Reserved space in logical pixels 保留空间（逻辑像素）
    readonly property real bottomInset: _insetFor(guard ? guard.bottomReservedHeight : 0)
    readonly property real topInset: _insetFor(guard ? guard.topReservedHeight : 0)
    property bool _watching: false
    property Connections _guardConnections: Connections {
        function onReservationsChanged() { control.reservationsChanged() }

        target: control.guard
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
    // Convert one physical reservation to logical pixels and drop the transparent margin
    // the banner window keeps above its visual card.
    // 将物理保留高度换算为逻辑像素，并扣除横幅窗口在卡片上方的透明边距。
    function _insetFor(physicalHeight) {
        if (!physicalHeight || physicalHeight <= 0) return 0
        var occupied = physicalHeight / _ratio
            - Enums.notification.layout.bannerWindowInset
        return occupied > 0 ? occupied + Enums.notification.layout.bannerGap : 0
    }
}
