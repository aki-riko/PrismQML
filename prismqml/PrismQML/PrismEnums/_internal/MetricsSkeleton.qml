// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// MetricsSkeleton - Skeleton placeholder metrics 骨架屏占位度量
// Static data only; kept in _internal so Metrics.qml stays inside its size gate.
// 仅静态数据; 放在 _internal 以保证 Metrics.qml 留在体积门禁内。
QtObject {
    id: skeleton

    // ==================== Public Props 公开属性 ====================
    readonly property int rectWidth: 200
    readonly property int rectHeight: 16
    readonly property int circleSize: 48
    readonly property real shimmerWidthRatio: 0.5
    readonly property int shimmerDurationMs: 1500
    readonly property int shimmerPauseMs: 500
    readonly property real baseAlphaLight: 0.06
    readonly property real baseAlphaDark: 0.08
    readonly property real shimmerAlphaLight: 0.04
    readonly property real shimmerAlphaDark: 0.12
    // QMLPage skeleton layout 懒加载页面骨架布局
    readonly property int pageHeaderHeight: 24 // Header bar height 标题条高度
    readonly property real pageHeaderWidthRatio: 0.4 // Header width share of the available width 标题条占可用宽度比例
    readonly property int pageRowHeight: 16 // Content row height 内容行高度
    readonly property real pageRowLongRatio: 0.9 // Long row width share 长行宽度比例
    readonly property real pageRowShortRatio: 0.6 // Short row width share 短行宽度比例
    readonly property int pageRowMinCount: 2 // Fewest content rows 最少内容行数
    readonly property int pageRowMaxCount: 16 // Most content rows 最多内容行数
    readonly property int pageCardHeight: 72 // Bottom card height 底部卡片高度
}
