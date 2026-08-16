// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// NotificationAnimatorGeometryUpdateTimer - Coalesce notification geometry updates
// NotificationAnimatorGeometryUpdateTimer - 合并通知几何更新
Timer {
    id: geometryUpdateTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "notificationAnimatorGeometryUpdateTimer"
    interval: Enums.duration.none
    repeat: false
    onTriggered: host.updatePosition()
}
