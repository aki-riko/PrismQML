// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "."
import "_internal" as ButtonLeafInternal

// RepeatButton - Button that keeps firing while held 按住期间持续触发的按钮
// Standalone leaf instead of a ButtonCore feature: held repeat owns a timer lifecycle,
// while ButtonCore features are mutually exclusive visual branches.
// 独立叶组件而非 ButtonCore 功能: 长按重复需要独立的计时器生命周期, 而 ButtonCore 的功能
// 分支是互斥的视觉分支。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property alias text: button.text
    property alias icon: button.icon
    property alias iconSize: button.iconSize
    property alias style: button.style
    property alias radius: button.radius
    property alias toolTipText: button.toolTipText
    property bool autoRepeat: true
    property int repeatDelay: Enums.duration.spinBoxRepeatDelay
    property int repeatInterval: Enums.duration.spinBoxRepeatInterval

    // ==================== Internal Props 内部属性 ====================
    readonly property bool _repeatRequested:
        autoRepeat && control.enabled && !button.loading && button.pressed

    // ==================== Readonly State 只读状态 ====================
    readonly property bool pressed: button.pressed
    readonly property bool repeating: repeatTimer.running

    // ==================== Signals 信号 ====================
    signal clicked()
    signal repeated()

    // ==================== Size 尺寸 ====================
    implicitWidth: button.implicitWidth
    implicitHeight: button.implicitHeight

    // ==================== Content 内容 ====================
    Button {
        id: button

        anchors.fill: parent
        enabled: control.enabled
        onClicked: control.clicked()
    }

    ButtonLeafInternal.RepeatButtonRepeatTimer {
        id: repeatTimer

        buttonControl: control
    }
}
