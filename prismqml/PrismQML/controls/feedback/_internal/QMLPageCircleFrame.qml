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
    property real minimumRadiusPixels: Enums.controlSize.navBarHeight / 2
    property bool revealTarget: false
    // Match the SplashScreen progress-ring stroke. 与 SplashScreen 进度环复用同一描边度量。
    property real borderWidthPixels: Enums.splashScreenMetrics.progressRingBorderWidth
    property color borderColor: Enums.accentColor

    // ==================== Readonly State 只读状态 ====================
    readonly property real aspectRatio: width / Math.max(height, 1)
    readonly property real minimumRadius: minimumRadiusPixels / Math.max(height, 1)
    readonly property real edgeSoftness:
        Enums.lazyLoadingTransitionMetrics.edgeSoftness / Math.max(height, 1)
    readonly property real borderWidth:
        borderWidthPixels / Math.max(height, 1)
    readonly property real invertMask: revealTarget
        ? Enums.opacityLevel.visible : Enums.opacityLevel.invisible

    blending: true
    fragmentShader: Qt.resolvedUrl("../../../shaders/qml_page_circle_transition.frag.qsb")
}
