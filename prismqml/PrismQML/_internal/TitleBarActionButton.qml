// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// TitleBarActionButton - Optional generic title-bar action 可选通用标题栏动作
// Hosts decide the action meaning; the window only owns placement and styling.
// 宿主决定动作含义；窗口只负责位置与样式。
Rectangle {
    id: control

    // ==================== Required Props 必需属性 ====================
    required property var targetWindow

    // ==================== Public Props 公开属性 ====================
    property string icon: ""
    property string toolTipText: ""
    property bool actionEnabled: true
    property int buttonWidth: Enums.window.captionButtonWidth
    property int buttonHeight: Enums.window.captionButtonHeight
    property int buttonRadius: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property bool hovered: actionEnabled && mouseArea.containsMouse
    readonly property bool pressed: actionEnabled && mouseArea.pressed
    readonly property color iconColor: Enums.isDark
        ? Enums.windowButtonColors.iconLight
        : Enums.windowButtonColors.iconDark

    // ==================== Signals 信号 ====================
    signal clicked()

    // ==================== Size 尺寸 ====================
    width: visible ? buttonWidth : 0
    height: buttonHeight
    radius: buttonRadius
    color: Enums.transparent
    opacity: actionEnabled ? Enums.opacityLevel.visible : Enums.opacityLevel.disabled
    Accessible.role: Accessible.Button
    Accessible.name: control.toolTipText || control.icon
    Accessible.onPressAction: {
        if (control.actionEnabled && control.visible) control.clicked()
    }

    // ==================== Content 内容 ====================
    Rectangle {
        anchors.fill: parent
        color: control.pressed
            ? (Enums.isDark
                ? Enums.windowButtonColors.normalPressedDark
                : Enums.windowButtonColors.normalPressedLight)
            : (control.hovered
                ? (Enums.isDark
                    ? Enums.windowButtonColors.normalHoverDark
                    : Enums.windowButtonColors.normalHoverLight)
                : Enums.transparent)
        radius: control.buttonRadius
    }

    Icon {
        anchors.centerIn: parent
        icon: control.icon
        iconSize: Enums.iconSize.m
        color: control.iconColor
        visible: control.icon !== ""
    }

    ToolTip {
        id: toolTip
        x: (parent.width - width) / 2
        y: parent.height
        text: control.toolTipText
        visible: control.hovered && control.actionEnabled && control.toolTipText !== ""
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: control.visible
        hoverEnabled: true
        onClicked: {
            if (control.actionEnabled) control.clicked()
        }
    }

}
