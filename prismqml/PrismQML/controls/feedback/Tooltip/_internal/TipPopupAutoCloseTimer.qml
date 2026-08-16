// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// TipPopupAutoCloseTimer - Close the tip after its configured duration 按配置时长自动关闭提示弹层
Timer {
    id: autoCloseTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "tipPopupAutoCloseTimer"
    interval: host.duration
    repeat: false
    onTriggered: host.close()
}
