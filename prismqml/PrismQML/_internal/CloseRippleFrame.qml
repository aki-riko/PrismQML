// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// CloseRippleFrame - Shared water-ripple dissolve renderer 共享水滴涟漪消失渲染器
ShaderEffect {
    id: effect

    // ==================== Public Props 公开属性 ====================
    property variant source: null
    property real progress: Enums.opacityLevel.invisible

    // ==================== Readonly State 只读状态 ====================
    readonly property real aspectRatio: width / Math.max(height, 1)
    readonly property real tailLength: Enums.windowCloseMetrics.rippleTailLength
    readonly property real waveFrequency: Enums.windowCloseMetrics.rippleWaveFrequency
    readonly property real waveDispersion: Enums.windowCloseMetrics.rippleWaveDispersion
    readonly property real waveDamping: Enums.windowCloseMetrics.rippleWaveDamping
    readonly property real waveAmplitude: Enums.windowCloseMetrics.rippleWaveAmplitude
    readonly property real highlightStrength: Enums.windowCloseMetrics.rippleHighlightStrength
    readonly property real frontSoftness: Enums.windowCloseMetrics.rippleFrontSoftness
    readonly property real frontRefractionWidth: Enums.windowCloseMetrics.rippleFrontRefractionWidth
    readonly property real crestSharpness: Enums.windowCloseMetrics.rippleCrestSharpness
    readonly property real rippleOpacity: Enums.windowCloseMetrics.rippleOpacity
    readonly property real finishFadeStart: Enums.windowCloseMetrics.rippleFinishFadeStart

    blending: true
    fragmentShader: Qt.resolvedUrl("../shaders/window_close_ripple.frag.qsb")
}
