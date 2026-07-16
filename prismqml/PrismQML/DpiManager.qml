// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

pragma Singleton
import QtQuick

// DpiManager - Handle high DPI screen scaling DPI管理器处理高DPI缩放
QtObject {
    id: dpiManager

    // ==================== Public Props 公开属性 ====================
    // Base DPI (design-time density, usually 96dpi) 基准DPI
    readonly property real baseDpi: 96

    // Current screen DPI (guard against undefined on headless/embedded) 当前屏幕DPI
    readonly property real screenDpi: (Screen && Screen.logicalPixelDensity) ? Screen.logicalPixelDensity * 25.4 : baseDpi

    // DPI scale factor DPI缩放因子
    readonly property real scale: Math.max(1.0, screenDpi / baseDpi)

    // Device pixel ratio (guard against undefined) 设备像素比
    readonly property real devicePixelRatio: (Screen && Screen.devicePixelRatio) ? Screen.devicePixelRatio : 1.0

    // User configured DPI scale (0=system, 100/125/150/175/200=fixed) 用户配置的DPI缩放
    readonly property int userDpiScale: (typeof ConfigManager !== "undefined" && ConfigManager) ? ConfigManager.dpiScale : 0
}
