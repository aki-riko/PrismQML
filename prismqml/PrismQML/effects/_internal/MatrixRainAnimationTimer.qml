// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// MatrixRainAnimationTimer - Drive rain drawing from presented frames
// MatrixRainAnimationTimer - 按实际呈现帧驱动数字雨绘制
FrameAnimation {
    id: animationTimer

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property var targetCanvas

    // ==================== Readonly State 只读状态 ====================
    // Preserve the old motion rate only; frame scheduling is refresh-driven.
    // 仅保留旧运动速率基准；帧调度已经改为跟随刷新率。
    readonly property real legacyIntervalMilliseconds:
        Math.max(16, 50 / host._safeSpeed)

    // ==================== Internal Props 内部属性 ====================
    property real _pendingStepScale: 0

    // ==================== Public Methods 公开方法 ====================
    function takeStepScale() {
        var stepScale = _pendingStepScale > 0 ? _pendingStepScale : 1
        _pendingStepScale = 0
        return stepScale
    }

    objectName: "matrixRainAnimationTimer"
    running: host.running && !host.paused && host.visible
    onRunningChanged: if (!running) _pendingStepScale = 0
    onTriggered: {
        var deltaMilliseconds = frameTime * 1000
        if (deltaMilliseconds <= 0) return
        _pendingStepScale += Math.min(
            1, deltaMilliseconds / legacyIntervalMilliseconds)
        targetCanvas.requestPaint()
    }
}
