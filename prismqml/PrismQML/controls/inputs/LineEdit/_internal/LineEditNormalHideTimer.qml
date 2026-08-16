// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// LineEditNormalHideTimer - Delay hiding the collapsible text field 可折叠输入框文本区域延迟隐藏计时器
Timer {
    id: hideTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "lineEditNormalHideTimer"
    interval: Enums.duration.medium
    repeat: false
    onTriggered: if (!host.expanded) host._textInputVisible = false
}
