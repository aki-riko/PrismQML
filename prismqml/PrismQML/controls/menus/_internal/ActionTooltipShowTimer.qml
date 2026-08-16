// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ActionTooltipShowTimer - Show an action tooltip after the hover delay 悬停延时后显示菜单动作提示
Timer {
    id: showTimer

    // ==================== Required Props 必需属性 ====================
    required property var actionControl
    required property var hoverArea
    required property var tooltip

    objectName: "actionTooltipShowTimer"
    interval: 600
    repeat: false
    running: actionControl.toolTip !== "" && hoverArea.containsMouse
    onTriggered: tooltip.show()
}
