// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../feedback/Progress/_internal"

// ButtonProgress - Progress bar features 进度条功能
// Internal module for Button Button内部模块
Item {
    id: progressFeature
    
    // ==================== Required Props 必需属性 ====================
    required property int feature
    required property int style
    required property real progress
    required property bool showProgress
    required property real parentRadius
    
    // ==================== Color Helper (same as ButtonContent ring) 颜色辅助 ====================
    // Primary/Filled/Gradient uses foreground color (white) Primary/Filled/Gradient使用前景色（白色）
    readonly property bool _useForegroundColor: style === Enums.button.style_primary ||
                                                style === Enums.button.style_filled ||
                                                style === Enums.button.style_gradient
    readonly property color _progressColor: _useForegroundColor ? Enums.accentForeground : Enums.accentColor
    readonly property color _trackColor: _useForegroundColor ? Enums.stateColor.onAccentOverlay : Enums.stateColor.progressTrack
    
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    height: Enums.border.thick
    
    // ==================== Progress Bar 进度条 ====================
    Item {
        id: progressBar
        anchors.fill: parent
        visible: feature === Enums.button.feature_progress_bar && progressFeature.showProgress

        // Background track 背景轨道
        Rectangle {
            anchors.fill: parent
            radius: height / 2
            color: progressFeature._trackColor
        }

        // Progress fill 进度填充
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: parent.width * progressFeature.progress
            radius: height / 2
            color: progressFeature._progressColor
        }
    }
    
    // ==================== Indeterminate Progress Bar 不确定进度条 ====================
    Item {
        id: indeterminateBar
        anchors.fill: parent
        clip: true
        visible: feature === Enums.button.feature_indeterminate_bar

        // Background track 背景轨道
        Rectangle {
            anchors.fill: parent
            radius: height / 2
            color: progressFeature._trackColor
        }

        // Indeterminate progress 不确定进度(单块加速穿梭)
        IndeterminateBarImpl {
            anchors.fill: parent
            color: progressFeature._progressColor
            radius: height / 2
            running: indeterminateBar.visible
        }
    }
}
