// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// SpinBoxAutoRepeatTimer - Repeat one spin direction while held
// SpinBoxAutoRepeatTimer - 按住期间重复执行一个微调方向
Timer {
    id: repeatTimer

    // ==================== Required Props 必需属性 ====================
    required property var spinControl

    // ==================== Internal Props 内部属性 ====================
    property bool _inRepeatPhase: false

    objectName: "spinBoxAutoRepeatTimer"
    interval: _inRepeatPhase
        ? spinControl._repeatCurrentInterval : spinControl.autoRepeatDelay
    repeat: _inRepeatPhase
    onTriggered: {
        if (!_inRepeatPhase) {
            spinControl._repeatCurrentInterval = spinControl.autoRepeatInterval
            _inRepeatPhase = true
            start()
            return
        }
        if (spinControl._repeatIsUp) spinControl.increase()
        else spinControl.decrease()
        // Accelerate each repeat toward the minimum interval 每次重复后向最短间隔收敛
        if (spinControl.autoRepeatMinInterval > 0
                && spinControl._repeatCurrentInterval
                    > spinControl.autoRepeatMinInterval) {
            var next = Math.max(
                spinControl.autoRepeatMinInterval,
                Math.floor(spinControl._repeatCurrentInterval
                    * Enums.input.spinBoxRepeatAcceleration)
            )
            if (next !== spinControl._repeatCurrentInterval) {
                spinControl._repeatCurrentInterval = next
            }
        }
    }
}
