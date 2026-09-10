// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import QtQuick.Window  // 置于库import后:原生Window名归库后不被覆盖
import QtQuick  // 置于库import后:去前缀后保原生类型不被覆盖

// DesktopOverlay - Desktop notification window with slide animation 带滑动动画的桌面通知窗口
// Provides desktop-level parent for Toast/InfoBar 为Toast/InfoBar提供桌面级parent
// Now uses shared NotificationAnimator for consistent animation 现在使用共享的NotificationAnimator保持动画一致
Window {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int position: Enums.notification.posBottomRight  // Nine-grid enum (0-8) 九宫格位置枚举
    property real stackOffset: 0  // Stack offset for multiple notifications 堆叠偏移
    property Item notificationItem: null  // Reference to notification for dynamic size 通知组件引用用于动态尺寸

    readonly property real contentWidth: notificationItem
        ? (notificationItem.implicitWidth > 0 ? notificationItem.implicitWidth : notificationItem.width)
        : Enums.controlSize.toastWidth
    readonly property real contentHeight: notificationItem ? (notificationItem.implicitHeight > 0 ? notificationItem.implicitHeight : notificationItem.height) : Enums.controlSize.toastHeight
    readonly property real _contentInset: Enums.spacing.xs / 2
    readonly property real _stackTopInset: _notificationStackInset("_stackTopInset")
    readonly property real _stackBottomInset: _notificationStackInset("_stackBottomInset")

    // ==================== Internal Props 内部属性 ====================
    // Windows notification banners sit in a higher window band (4) than any ordinary topmost
    // window (1) and cannot be covered, so bottom-anchored desktop notifications reserve the
    // height those banners occupy.
    // Windows通知横幅位于比普通topmost窗口更高的窗口层带(4)且无法被压过，
    // 因此底部锚定的桌面通知保留这些横幅占用的高度。
    readonly property var _bannerGuard: (typeof NotificationBannerGuard !== "undefined" && NotificationBannerGuard)
        ? NotificationBannerGuard : null
    readonly property real _bannerInset: {  // Reserved bottom space in logical pixels 底部保留高度（逻辑像素）
        if (!_bannerGuard || _bannerGuard.reservedHeight <= 0) return 0
        var ratio = screen ? screen.devicePixelRatio : 1
        if (ratio <= 0) ratio = 1
        // The banner window rect carries a transparent margin above the visual card
        // (measured 30 DIP: 228px window = 107px card + 30px top + 15px bottom at 150%),
        // so that margin must be subtracted before reserving space.
        // 横幅窗口矩形在卡片上方含透明边距（150%缩放下实测：窗口228px = 卡片107 + 上30 + 下15），
        // 保留空间前必须扣除该边距。
        var occupied = _bannerGuard.reservedHeight / ratio
            - Enums.notification.layout.bannerWindowInset
        return occupied > 0 ? occupied + Enums.notification.layout.bannerGap : 0
    }
    // Folded into the animator stack offset so the shared animator stays untouched
    // 并入动画器的堆叠偏移，使共享动画器保持原样
    readonly property real _animatorOffset: stackOffset
        + (Enums.notification.isBottom(position) ? _bannerInset : 0)
    property bool _bannerWatching: false
    
    // ==================== Signals 信号 ====================
    signal closed()

    // ==================== Public Methods 公开方法 ====================
    function show() {
        _acquireBannerWatch()
        animator.show()
    }

    function hide() {
        animator.hide()
    }

    // Update position when stack changes 堆叠变化时更新位置
    function updatePosition() {
        animator.updatePosition()
    }

    function _notificationStackInset(propertyName) {
        if (!notificationItem) return 0
        var inset = notificationItem[propertyName]
        if (inset === undefined || inset === null) return 0
        return _contentInset + inset
    }

    // ==================== Internal Methods 内部方法 ====================
    // Watch banner presence only while a desktop notification is on screen
    // 仅在桌面通知显示期间监视系统通知横幅
    function _acquireBannerWatch() {
        if (_bannerWatching || !_bannerGuard) return
        _bannerWatching = true
        _bannerGuard.acquire()
    }

    function _releaseBannerWatch() {
        if (!_bannerWatching || !_bannerGuard) return
        _bannerWatching = false
        _bannerGuard.release()
    }

    // Window settings 窗口设置
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    visible: false
    color: Enums.transparent
    width: contentWidth + _contentInset * 2  // Follow actual notification width 跟随通知实际宽度
    height: contentHeight + _contentInset * 2  // Use actual content height 使用实际内容高度

    // ==================== Content 内容 ====================
    // Shared animator 共享动画器
    property alias animator: animator
    NotificationAnimator {
        id: animator
        target: control
        position: control.position
        desktopMode: true  // Use screen coordinates 使用屏幕坐标
        stackOffset: control._animatorOffset
        onHideFinished: {
            control._releaseBannerWatch()
            control.visible = false
            control.closed()
        }
    }

    // Content area: Toast/InfoBar will be created here 内容区域：Toast/InfoBar 将被创建在这里
    property alias content: container
    Item {
        id: container
        anchors.fill: parent
    }

    // Re-anchor when the reserved banner height changes 通知横幅保留高度变化时重新定位
    Connections {
        function onReservedHeightChanged() { control.updatePosition() }

        target: control._bannerGuard
        ignoreUnknownSignals: true
    }

    // Re-anchor after a screen scaling ratio change 屏幕缩放比例变化后重新定位
    Connections {
        function onDevicePixelRatioChanged() { control.updatePosition() }

        target: control.screen
        ignoreUnknownSignals: true
    }

    Component.onDestruction: _releaseBannerWatch()
}
