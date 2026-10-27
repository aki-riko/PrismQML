// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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
    // Public component fallback: direct callers retain the global token set.
    // 公开组件回退：直接调用方继续使用全局 token。
    property var skinContext: Enums
    
    // ==================== Readonly State 只读状态 ====================
    // Color helpers shared with the ButtonContent ring 与 ButtonContent 圆环一致的颜色辅助
    // Primary/Filled/Gradient uses foreground color (white) Primary/Filled/Gradient使用前景色（白色）
    readonly property bool _useForegroundColor: style === skinContext.button.style_primary ||
                                                style === skinContext.button.style_filled ||
                                                style === skinContext.button.style_gradient
    readonly property color _progressColor: _useForegroundColor ? skinContext.accentForeground : skinContext.accentColor
    readonly property color _trackColor: _useForegroundColor ? skinContext.stateColor.onAccentOverlay : skinContext.stateColor.progressTrack
    
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    height: skinContext.border.thick
    
    // ==================== Content 内容 ====================
    // Progress bar 进度条
    Item {
        id: progressBar
        anchors.fill: parent
        visible: feature === skinContext.button.feature_progress_bar && progressFeature.showProgress

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
    
    // Indeterminate progress bar 不确定进度条
    Item {
        id: indeterminateBar
        anchors.fill: parent
        clip: true
        visible: feature === skinContext.button.feature_indeterminate_bar

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
