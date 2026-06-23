// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Carousel - Carousel enums 轮播图枚举
// 两个正交维度：effect(视觉效果) × orientation(方向，由组件的 orientation: Qt.Horizontal/Vertical 控制)。
QtObject {
    // Effect 视觉效果(与 orientation 正交)
    readonly property int effect_peek: 0       // Fluent 商店式 slide+peek 露边(默认)
    readonly property int effect_slide: 1      // 普通整图滑动 plain slide

    // Navigation button position 导航按钮位置
    readonly property int nav_inside: 0        // Inside carousel 内部
    readonly property int nav_outside: 1       // Outside carousel 外部

    // ==================== Peek Animation 露边动画参数 ====================
    // Based on Fluent Design carousel peek effect 基于Fluent Design轮播露边效果
    readonly property real peekScale: 0.85              // Adjacent item scale 相邻项缩放比例
    readonly property real peekOpacity: 0.6             // Adjacent item opacity 相邻项透明度
    readonly property real peekRatio: 0.15              // Visible ratio of adjacent items 相邻项可见比例
    readonly property real peekSpacing: 0.02            // Gap ratio between items 项目间隙比例
}
