// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// PivotIndicatorSyncTimer - Retry indicator geometry after delegate rebuilds
// PivotIndicatorSyncTimer - 委托重建后重试指示器几何同步
Timer {
    id: indicatorSyncTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "pivotIndicatorSyncTimer"
    interval: Enums.duration.tick
    repeat: true
    onTriggered: host._updateIndicatorWithAnimation()
}
