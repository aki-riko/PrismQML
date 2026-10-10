// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// RepeatButtonRepeatTimer - Held-repeat timer for RepeatButton RepeatButton 的长按重复计时器
// The first tick waits for repeatDelay, every later tick follows repeatInterval.
// 首次触发等待 repeatDelay, 之后每次触发按 repeatInterval 进行。
Timer {
    id: repeatTimer

    // ==================== Required Props 必需属性 ====================
    required property var buttonControl

    // ==================== Internal Props 内部属性 ====================
    property bool _inRepeatPhase: false

    objectName: "repeatButtonRepeatTimer"
    running: buttonControl._repeatRequested
    interval: _inRepeatPhase
        ? buttonControl.repeatInterval : buttonControl.repeatDelay
    // A repeating timer never clears its own running flag, so the bound `running` above
    // survives the first tick; a single-shot timer would overwrite that binding.
    // 重复计时器不会自行清除 running, 因此上面的 running 绑定能在首次触发后存活;
    // 单次计时器会覆写该绑定。
    repeat: true
    onRunningChanged: if (!running) _inRepeatPhase = false
    onTriggered: {
        if (!_inRepeatPhase) {
            // The first tick ends the delay phase; the interval change restarts this timer
            // 首次触发结束延迟阶段; 间隔变化会让本计时器按重复间隔重新开始
            _inRepeatPhase = true
            return
        }
        buttonControl.repeated()
        buttonControl.clicked()
    }
}
