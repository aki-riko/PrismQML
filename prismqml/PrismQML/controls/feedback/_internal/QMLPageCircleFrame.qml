// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// QMLPageCircleFrame - Single-aperture loading transition renderer 单层光圈加载过渡渲染器
ShaderEffect {
    id: effect

    // ==================== Public Props 公开属性 ====================
    property variant source: null
    property real progress: Enums.opacityLevel.invisible
    property real minimumRadiusPixels: 0
    property bool revealTarget: false
    // Match the SplashScreen progress-ring stroke. 与 SplashScreen 进度环复用同一描边度量。
    property real borderWidthPixels: Enums.splashScreenMetrics.progressRingBorderWidth
    // Gated by _strokeVisibility so a closed aperture draws no center dot.
    // 受 _strokeVisibility 约束, 闭合光圈不会画出中心点。
    property color borderColor: Qt.rgba(
        Enums.accentColor.r,
        Enums.accentColor.g,
        Enums.accentColor.b,
        Enums.accentColor.a * _strokeVisibility)

    // ==================== Readonly State 只读状态 ====================
    readonly property real aspectRatio: width / Math.max(height, 1)
    readonly property real minimumRadius: minimumRadiusPixels / Math.max(height, 1)
    readonly property real edgeSoftness:
        Enums.lazyLoadingTransitionMetrics.edgeSoftness / Math.max(height, 1)
    readonly property real borderWidth:
        borderWidthPixels / Math.max(height, 1)
    // The shader outlines the aperture at abs(distance - apertureRadius), so an
    // aperture narrower than the stroke's own half-width paints a filled dot at the
    // center instead of a ring. Fade the stroke out over that range: a ring thinner
    // than its stroke is not a ring. 着色器按 abs(distance - apertureRadius) 描边,
    // 因此光圈比描边半宽还窄时画出的是中心实心点而非环。在该区间内淡出描边: 比自身
    // 描边还细的环不是环。
    readonly property real _apertureRadiusPixels:
        minimumRadiusPixels
        + (Math.sqrt(width * width + height * height) * 0.5
           + Enums.lazyLoadingTransitionMetrics.edgeSoftness * 2
           - minimumRadiusPixels)
          * Math.max(0, Math.min(1, progress))
    readonly property real _strokeVisibility:
        borderWidthPixels <= 0
            ? Enums.opacityLevel.invisible
            : Math.max(0, Math.min(1, _apertureRadiusPixels / borderWidthPixels))
    readonly property real invertMask: revealTarget
        ? Enums.opacityLevel.visible : Enums.opacityLevel.invisible

    blending: true
    fragmentShader: Qt.resolvedUrl("../../../shaders/qml_page_circle_transition.frag.qsb")
}
