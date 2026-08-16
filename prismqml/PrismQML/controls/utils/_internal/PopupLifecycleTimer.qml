// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import "PopupLifecycle.js" as PopupLifecycle
import QtQuick

// PopupLifecycleTimer - Complete delayed popup lifecycle transitions
// PopupLifecycleTimer - 完成延迟弹层生命周期转换
Timer {
    id: lifecycleTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    interval: Enums.popupMetrics.showAnimDelayMs
    onTriggered: PopupLifecycle.onTimer(host)
}
