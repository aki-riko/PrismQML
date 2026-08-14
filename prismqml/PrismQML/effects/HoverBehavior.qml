// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// HoverBehavior - Animated hover entry with immediate exit 悬浮进入动画与立即退出
Behavior {
    id: root

    required property bool active
    property bool animationEnabled: true
    property int enterDuration: Enums.duration.fast
    property int easingType: Easing.Linear
    property bool _previousActive: false

    function _commitActive() {
        _previousActive = active
    }

    enabled: animationEnabled
    onActiveChanged: Qt.callLater(root._commitActive)

    PropertyAnimation {
        // Read a one-event delayed snapshot so binding notification order cannot reverse the direction.
        // 读取延后一事件轮的快照，避免绑定通知顺序颠倒进入/退出方向。
        duration: root._previousActive
                  ? Enums.motion.hoverExitDuration : root.enterDuration
        easing.type: root.easingType
    }
}
