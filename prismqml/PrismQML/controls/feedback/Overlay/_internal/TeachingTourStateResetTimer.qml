// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// TeachingTourStateResetTimer - Clear the inactive tour index after tip hiding
// TeachingTourStateResetTimer - 提示隐藏后清理非活动指引索引
Timer {
    id: stateResetTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "teachingTourStateResetTimer"
    interval: Enums.duration.tipHide
    repeat: false
    onTriggered: if (!host._active) host._currentIndex = -1
}
