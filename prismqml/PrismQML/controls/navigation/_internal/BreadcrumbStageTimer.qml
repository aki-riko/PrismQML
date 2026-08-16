// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// BreadcrumbStageTimer - Run and release an on-demand breadcrumb stage 按需执行并释放面包屑阶段
Timer {
    id: stageTimer

    // ==================== Required Props 必需属性 ====================
    required property int timerInterval
    required property var triggerCallback
    required property var releaseCallback

    objectName: "breadcrumbStageTimer"
    interval: timerInterval
    repeat: false
    onTriggered: {
        triggerCallback()
        releaseCallback(stageTimer)
        destroy()
    }
}
