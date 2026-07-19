// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import QtQuick.Window  // 置于库import后:原生Window名归库后不被覆盖
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// DesktopOverlay - Desktop notification window with slide animation 带滑动动画的桌面通知窗口
// Provides desktop-level parent for Toast/InfoBar 为Toast/InfoBar提供桌面级parent
// Now uses shared NotificationAnimator for consistent animation 现在使用共享的NotificationAnimator保持动画一致
Window {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int position: Enums.notification.posBottomRight  // 0-5 位置枚举
    property real stackOffset: 0  // Stack offset for multiple notifications 堆叠偏移
    property Item notificationItem: null  // Reference to notification for dynamic size 通知组件引用用于动态尺寸

    readonly property real contentWidth: notificationItem
        ? (notificationItem.implicitWidth > 0 ? notificationItem.implicitWidth : notificationItem.width)
        : Enums.controlSize.toastWidth
    readonly property real contentHeight: notificationItem ? (notificationItem.implicitHeight > 0 ? notificationItem.implicitHeight : notificationItem.height) : Enums.controlSize.toastHeight
    
    // ==================== Signals 信号 ====================
    signal closed()

    // ==================== Public Methods 公开方法 ====================
    function show() {
        animator.show()
    }

    function hide() {
        animator.hide()
    }

    // Update position when stack changes 堆叠变化时更新位置
    function updatePosition() {
        animator.updatePosition()
    }

    // Window settings 窗口设置
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    visible: false
    color: Enums.transparent
    width: contentWidth + Enums.spacing.xs  // Follow actual notification width 跟随通知实际宽度
    height: contentHeight + Enums.spacing.xs  // Use actual content height 使用实际内容高度

    // ==================== Content 内容 ====================
    // Shared animator 共享动画器
    property alias animator: animator
    NotificationAnimator {
        id: animator
        target: control
        position: control.position
        desktopMode: true  // Use screen coordinates 使用屏幕坐标
        stackOffset: control.stackOffset
        onHideFinished: { control.visible = false; control.closed() }
    }

    // Content area: Toast/InfoBar will be created here 内容区域：Toast/InfoBar 将被创建在这里
    property alias content: container
    Item {
        id: container
        anchors.fill: parent
    }
}
