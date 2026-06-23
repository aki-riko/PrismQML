// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

pragma Singleton
import QtQuick

// DpiManager - Handle high DPI screen scaling DPI管理器处理高DPI缩放
QtObject {
    id: dpiManager
    
    // Base DPI (design-time density, usually 96dpi) 基准DPI
    readonly property real baseDpi: 96
    
    // Current screen DPI (guard against undefined on headless/embedded) 当前屏幕DPI
    readonly property real screenDpi: (Screen && Screen.logicalPixelDensity) ? Screen.logicalPixelDensity * 25.4 : baseDpi
    
    // DPI scale factor DPI缩放因子
    readonly property real scale: Math.max(1.0, screenDpi / baseDpi)
    
    // Device pixel ratio (guard against undefined) 设备像素比
    readonly property real devicePixelRatio: (Screen && Screen.devicePixelRatio) ? Screen.devicePixelRatio : 1.0
    
    // User configured DPI scale (0=system, 100/125/150/175/200=fixed) 用户配置的DPI缩放
    readonly property int userDpiScale: ConfigManager ? ConfigManager.dpiScale : 0
    
    // Effective scale factor 综合缩放因子
    // 0=跟随系统(devicePixelRatio), >0=用户指定比例
    readonly property real effectiveScale: {
        if (userDpiScale > 0) {
            return userDpiScale / 100.0
        }
        return Math.max(1.0, devicePixelRatio)
    }
    
    // Convert dp to pixels (device-independent to physical) dp转像素
    function dp(value) {
        return Math.round(value * effectiveScale)
    }
    
    // Convert sp to pixels (for font size) sp转像素用于字体
    function sp(value) {
        return Math.round(value * effectiveScale)
    }
    
    // Predefined common sizes 预定义常用尺寸
    readonly property int spacing2: dp(2)
    readonly property int spacing4: dp(4)
    readonly property int spacing8: dp(8)
    readonly property int spacing12: dp(12)
    readonly property int spacing16: dp(16)
    readonly property int spacing24: dp(24)
    readonly property int spacing32: dp(32)
    
    // Predefined font sizes 预定义字体大小
    readonly property int fontSmall: sp(12)
    readonly property int fontNormal: sp(14)
    readonly property int fontLarge: sp(16)
    readonly property int fontTitle: sp(20)
    readonly property int fontLargeTitle: sp(28)
    
    // Predefined component heights 预定义组件高度
    readonly property int buttonHeight: dp(32)
    readonly property int inputHeight: dp(32)
    readonly property int cardPadding: dp(16)
    readonly property int borderRadius: dp(4)
    readonly property int borderRadiusLarge: dp(8)
}
