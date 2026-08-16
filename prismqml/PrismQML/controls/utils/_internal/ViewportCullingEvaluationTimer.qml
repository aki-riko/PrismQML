// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ViewportCullingEvaluationTimer - Periodically evaluate viewport visibility
// ViewportCullingEvaluationTimer - 周期性评估视口可见性
Timer {
    id: evaluationTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "viewportCullingTimer"
    interval: 150
    running: host._flickable !== null && host._hostWindowExposed
    repeat: true
    triggeredOnStart: true
    onTriggered: host._updateVisibility()
}
