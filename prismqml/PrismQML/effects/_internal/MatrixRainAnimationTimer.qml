// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// MatrixRainAnimationTimer - Request the next rain frame
// MatrixRainAnimationTimer - 请求下一帧数字雨绘制
Timer {
    id: animationTimer

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property var targetCanvas

    objectName: "matrixRainAnimationTimer"
    interval: Math.max(16, 50 / host._safeSpeed)
    running: host.running && !host.paused && host.visible
    repeat: true
    onTriggered: targetCanvas.requestPaint()
}
