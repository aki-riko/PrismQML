// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ScrollViewportPhaseTimer - Run the active viewport measurement phase 执行当前视口测量阶段
Timer {
    id: phaseTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "scrollViewportPhaseTimer"
    interval: host._phase === host._phaseContentUpdate
              ? Enums.duration.fast
              : (host._phase === host._phaseSuppressionClear
                 ? Enums.duration.instant : Enums.duration.none)
    repeat: false
    onTriggered: host._runPhase()
}
