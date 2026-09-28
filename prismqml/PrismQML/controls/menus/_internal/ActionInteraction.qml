// ActionInteraction - Pointer and tooltip interaction 菜单动作指针与提示交互
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../feedback/Tooltip"

Item {
    id: interaction

    required property var actionControl
    readonly property alias hoverArea: itemArea

    objectName: "actionInteraction"
    anchors.fill: parent

    Loader {
        id: tipLoader

        objectName: "actionTooltipLoader"
        active: interaction.actionControl.toolTip !== ""
            && (itemArea.containsMouse || item !== null)
        sourceComponent: TooltipCore {
            id: actionTooltip

            text: interaction.actionControl.toolTip
            x: itemArea.mouseX + Enums.spacing.m
            y: interaction.actionControl.height + Enums.spacing.xxs

            ActionTooltipShowTimer {
                id: tooltipShowTimer

                actionControl: interaction.actionControl
                hoverArea: itemArea
                tooltip: actionTooltip
            }
        }
    }

    MouseArea {
        id: itemArea
        anchors.fill: parent
        hoverEnabled: !Touch.isTouch
        enabled: interaction.actionControl.enabled
        cursorShape: Qt.ArrowCursor
        onPressed: {
            interaction.actionControl._stabilizePopupAncestor()
            interaction.actionControl.pressed()
        }
        onContainsMouseChanged: {
            if (!containsMouse && tipLoader.item) tipLoader.item.hide()
        }
        onClicked: {
            if (interaction.actionControl.hasSubmenu) {
                interaction.actionControl.submenuRequested()
                return
            }
            if (interaction.actionControl.checkable) {
                interaction.actionControl.checked = !interaction.actionControl.checked
            }
            interaction.actionControl.triggered()
        }
    }
}
