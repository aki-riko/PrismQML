// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../"

// AutoUpdaterToastSyncTimer - Coalesce feedback model updates into one sync
// AutoUpdaterToastSyncTimer - 将反馈模型更新合并为一次同步
Timer {
    id: syncTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "autoUpdaterToastSyncTimer"
    interval: Enums.duration.none
    onTriggered: host._sync()
}
