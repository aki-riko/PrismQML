// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// PopupPositionUpdateTimer - Coalesce one popup position update
// PopupPositionUpdateTimer - 合并一次弹层位置更新
Timer {
    id: updateTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "popupPositionUpdateTimer"
    interval: 0
    repeat: false
    onTriggered: host._updatePosition()
}
