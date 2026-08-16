// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// NavigationMicaReapplyTimer - Restore Mica after a window transition
// NavigationMicaReapplyTimer - 窗口状态变化后恢复 Mica
Timer {
    id: micaReapplyTimer

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property bool late

    interval: late ? Enums.window.micaLateReapplyDelayMs
                   : Enums.window.micaReapplyDelayMs
    onTriggered: host._applyMicaEffect(
        (late ? "late-restore:" : "restore:") + host._micaReapplyReason)
}
