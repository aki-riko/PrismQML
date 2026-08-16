// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ConfettiSpawnTimer - Spawn particle batches while the effect is active
// ConfettiSpawnTimer - 效果活动期间分批生成粒子
Timer {
    id: spawnTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "confettiSpawnTimer"
    interval: 5
    repeat: true
    running: host.running && host._spawnIndex < host.particleCount
    onTriggered: host._spawnBatch(8)
}
