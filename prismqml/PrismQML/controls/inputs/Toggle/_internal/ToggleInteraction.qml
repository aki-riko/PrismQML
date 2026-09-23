// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ToggleInteraction - Toggle pointer and tooltip lifecycle 交互与工具提示生命周期
Item {
    id: interaction

    // ==================== Required Props 必需属性 ====================
    required property var toggleControl
    readonly property bool containsMouse: mouseArea.containsMouse
    readonly property bool pressed: mouseArea.pressed

    // ==================== Size 尺寸 ====================
    anchors.fill: parent

    // ==================== Content 内容 ====================
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: interaction.toggleControl.enabled
            && !interaction.toggleControl._isSwitch
        hoverEnabled: true
        onClicked: interaction.toggleControl._handleClick()
    }

    HoverHandler {
        enabled: interaction.toggleControl.toolTipText !== "" && !Touch.isTouch
        onHoveredChanged: {
            if (hovered) {
                interaction.toggleControl._startToolTipShowTimer()
            } else {
                interaction.toggleControl._stopToolTipShowTimer()
                interaction.toggleControl._startToolTipHideTimer()
            }
        }
    }
}
