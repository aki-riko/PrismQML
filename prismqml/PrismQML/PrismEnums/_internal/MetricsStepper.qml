// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// MetricsStepper - Stepper step metrics 步骤条度量
// Static data only: the Stepper showcase geometry lives here so Metrics.qml
// keeps its public namespace while staying inside the modularization gate.
// 仅静态数据: 步骤条展示几何集中于此, 让 Metrics.qml 保留公开命名空间的同时留在模块化门禁内。
QtObject {
    id: stepper

    // ==================== Public Props 公开属性 ====================
    readonly property real baseScale: 1.0
    readonly property real tiltPeak: 4
    readonly property real railThicknessRatio: 0.14
    readonly property real completedGlowScale: 1.22
    readonly property real hoverScale: 1.08
    readonly property var haloScales: [1.0, 1.18, 1.38, 1.6, 1.85]
    readonly property real haloFalloff: 0.2
    readonly property real minBreath: 0.55
    readonly property real maxBreath: 1.0
    readonly property real rippleStartScale: 1.0
    readonly property real rippleEndScale: 2.3
    readonly property real particleSizeRatio: 0.12
    readonly property real particleDistanceRatio: 0.85
    readonly property real ringStartScale: 0.7
    readonly property real ringEndScale: 1.9
    readonly property real particleEndScale: 0.4
}
