// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import QtQuick

// PopupPrewarmTimer - Defer popup surface prewarming
// PopupPrewarmTimer - 延迟执行弹层表面预热
Timer {
    id: prewarmTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    interval: 0
    onTriggered: host._doPrewarm()
}
