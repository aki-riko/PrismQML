// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// MetricsMask - Mask threshold metrics 遮罩阈值度量
QtObject {
    id: mask

    // ==================== Public Props 公开属性 ====================
    readonly property real thresholdMin: 0.5 // Mask threshold minimum 遮罩阈值最小值
    readonly property real spreadAtMin: 0.0 // Mask spread at minimum 遮罩最小扩散
    readonly property real thresholdFull: 0.0 // Full mask threshold 完全遮罩阈值
    readonly property real spreadFull: 1.0 // Full mask spread 完全遮罩扩散
}
