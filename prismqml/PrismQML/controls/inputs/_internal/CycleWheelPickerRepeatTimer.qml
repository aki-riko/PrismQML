// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// CycleWheelPickerRepeatTimer - Repeat wheel scrolling while a button is held
// CycleWheelPickerRepeatTimer - 按住按钮期间重复滚动滚轮
Timer {
    id: repeatTimer

    // ==================== Required Props 必需属性 ====================
    required property var wheelControl

    objectName: "cycleWheelPickerRepeatTimer"
    interval: wheelControl._repeatStarted
        ? Enums.duration.wheelPickerRepeatInterval
        : Enums.duration.wheelPickerRepeatDelay
    repeat: true
    onTriggered: wheelControl._triggerRepeat()
}
