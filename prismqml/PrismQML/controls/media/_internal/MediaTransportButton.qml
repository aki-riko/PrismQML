// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"

// MediaTransportButton - Compact transport control 紧凑播放控制按钮
// Leaf control: it only needs its icon name, so no host reference is required.
// 叶子控件：只需要图标名，因此不需要宿主引用。
Item {
    id: control

    // ==================== Required Props 必需属性 ====================
    required property string iconName

    // ==================== Public Props 公开属性 ====================
    property color color: Enums.textColor.primary

    // ==================== Readonly State 只读状态 ====================
    readonly property bool hovered: pointerArea.containsMouse
    readonly property bool pressed: pointerArea.pressed
    // Touch has no hover preview: on touch the feedback follows the press
    // 触摸没有 hover 预览：触摸端反馈只在按压时生效，避免松手后残留
    readonly property bool _touchActive: Touch.feedback(hovered, pressed)

    // ==================== Signals 信号 ====================
    signal clicked()

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.inputHeightCompact
    implicitHeight: Enums.controlSize.inputHeightCompact
    width: implicitWidth
    height: implicitHeight

    // ==================== Content 内容 ====================
    Rectangle {
        anchors.fill: parent
        radius: Enums.radius.small
        color: control.pressed
            ? Enums.pressedColor
            : (control._touchActive
                ? Enums.hoverColor
                : Enums.withAlpha(Enums.dialogColor, Enums.opacityLevel.invisible))
    }

    Icon {
        anchors.centerIn: parent
        icon: control.iconName
        iconSize: Enums.iconSize.s
        color: control.color
    }

    MouseArea {
        id: pointerArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: control.clicked()
    }
}
