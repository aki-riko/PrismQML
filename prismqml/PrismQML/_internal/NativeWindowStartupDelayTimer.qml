// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// NativeWindowStartupDelayTimer - Defer native startup hook attempts
// NativeWindowStartupDelayTimer - 延迟执行原生启动钩子尝试
Timer {
    id: delayTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "nativeWindowStartupDelayTimer"
    interval: Enums.duration.instant
    onTriggered: host._attemptNativeHook()
}
