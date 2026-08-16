// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// NavigationMicaBackdropCommitTimer - Commit a successful Mica backdrop
// NavigationMicaBackdropCommitTimer - 提交成功的 Mica 背板状态
Timer {
    id: backdropCommitTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    interval: Enums.window.micaReapplyDelayMs
    onTriggered: {
        if (host._micaActive && host._nativeHookReady &&
                host._micaNativeApplySucceeded) {
            host._micaBackdropReady = true
        }
    }
}
