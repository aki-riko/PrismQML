// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Notification - Notification mode enums 通知模式枚举
QtObject {
    readonly property int mode_in_app: 0
    readonly property int mode_desktop: 1
    
    // ==================== Orientation 方向枚举 ====================
    // InfoBar/Toast layout orientation 布局方向
    // Supports Qt.Horizontal (1) / Qt.Vertical (2) standard enums 支持Qt标准枚举
    readonly property int orient_horizontal: Qt.Horizontal  // Horizontal layout 水平布局 (1)
    readonly property int orient_vertical: Qt.Vertical      // Vertical layout 垂直布局 (2)
    
    // InfoBar/Toast feature types InfoBar/Toast功能类型
    readonly property int feature_normal: 0           // Normal mode 普通模式
    readonly property int feature_progress_bar: 1     // Progress bar 进度条
    readonly property int feature_indeterminate_bar: 2 // Indeterminate progress bar 不确定进度条
    readonly property int feature_progress_ring: 3    // Progress ring 进度环
    readonly property int feature_indeterminate_ring: 4 // Indeterminate progress ring 不确定进度环
    
    // ==================== Animation Config 动画配置 ====================
    // Shared animation settings for NotificationAnimator and DesktopOverlay 供 NotificationAnimator 和 DesktopOverlay 共享的动画配置

    readonly property QtObject animation: QtObject {
        readonly property int showDuration: 300   // Show animation duration 显示动画时长
        readonly property int hideDuration: 250   // Hide animation duration 隐藏动画时长
        readonly property int repositionDuration: 300  // Stack reposition duration 堆叠补位动画时长
        readonly property int showEasing: Easing.OutBack   // Show easing type 显示缓动类型
        readonly property real showOvershoot: 0.8          // Subtle bounce (default 1.70158) 轻微回弹
        readonly property int hideEasing: Easing.InQuint   // Hide easing type 隐藏缓动类型
        readonly property int repositionEasing: Easing.OutCubic  // Reposition easing 补位缓动类型
    }
    
    // ==================== Layout Config 布局配置 ====================
    // Shared layout settings for notification positioning 通知定位共享布局配置
    readonly property QtObject layout: QtObject {
        readonly property int edgeMargin: 16      // Edge margin for slide animation 滑动动画边缘间距
        readonly property int verticalSlideExtra: 48  // Extra offset for top/bottom slide 正上/下方滑入额外偏移
        readonly property int screenMargin: 24    // Screen edge margin 屏幕边缘间距
        readonly property int windowMargin: 28    // In-window notification margin 窗口内通知边距
        readonly property int stackGapLarge: 25   // InfoBar stack gap InfoBar堆叠间距
        readonly property int stackGapSmall: 8    // Toast/Desktop stack gap Toast/桌面堆叠间距
        readonly property int taskbarOffset: 40   // Bottom taskbar offset 底部任务栏偏移
        readonly property int maxVisible: 5       // Max visible notifications 最大可见通知数
    }
    
    // ==================== Position Constants 位置常量 ====================
    // Shared position enum for all notification components 所有通知组件共享的位置枚举
    readonly property int posTopLeft: 0
    readonly property int posTop: 1
    readonly property int posTopRight: 2
    readonly property int posBottomLeft: 3
    readonly property int posBottom: 4
    readonly property int posBottomRight: 5
    
    // Position helper functions 位置辅助函数
    function isTop(pos) { return pos <= 2 }
    function isBottom(pos) { return pos >= 3 }
    function isLeft(pos) { return pos === 0 || pos === 3 }
    function isRight(pos) { return pos === 2 || pos === 5 }
    function isCenter(pos) { return pos === 1 || pos === 4 }
    
    // ==================== Severity Helpers 语义辅助函数 ====================
    // Map severity string to level number 映射severity字符串到level数字
    // Shared by Toast, InfoBarCore, DesktopNotification 供Toast/InfoBarCore/DesktopNotification共享
    function getSeverityLevel(severity) {
        switch (severity) {
            case "success": return 1
            case "warning": return 2
            case "error": return 3
            case "attention": return 4
            case "processing": return 5
            default: return 0  // info
        }
    }
    
    // Map severity to icon name 映射severity到图标名
    // Shared by Toast, InfoBarCore, DesktopNotification 供Toast/InfoBarCore/DesktopNotification共享
    function getSeverityIcon(severity) {
        switch (severity) {
            case "success": return "CheckmarkCircle"
            case "warning": return "Warning"
            case "error": return "DismissCircle"
            case "attention": return "Important"
            case "processing": return "ArrowSync"
            default: return "Info"
        }
    }
}
