// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../containers"
import "../../buttons"

// CommandBarFlyoutSurface - Command rows of one command bar flyout 命令浮出层的命令行
// The primary row reuses CommandBar; the secondary row is the mini-expanded panel.
// 主命令行复用 CommandBar; 次命令行即迷你展开面板。
Item {
    id: surface

    // ==================== Required Props 必需属性 ====================
    required property var flyout

    // ==================== Readonly State 只读状态 ====================
    readonly property var _skin: flyout.effectiveSkinContext
    readonly property bool _hasSecondary: flyout._hasSecondaryCommands
    readonly property bool _showSecondary: flyout.expanded
    // A secondary command without an icon must keep its label in the compact state.
    // 没有图标的次命令在紧凑状态下必须保留文字。
    readonly property bool _showSecondaryLabels: flyout.fullyExpanded

    // ==================== Internal Methods 内部方法 ====================
    function _secondaryText(command) {
        if (!command) return ""
        var label = command.text || ""
        if (_showSecondaryLabels || !command.icon) return label
        return ""
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: Math.max(
        _skin.controlSize.menuMinWidth,
        Math.max(primaryRow.implicitWidth, secondaryRow.implicitWidth))
    implicitHeight: contentColumn.implicitHeight

    // ==================== Content 内容 ====================
    Column {
        id: contentColumn

        width: surface.width
        spacing: surface._skin.spacing.xs

        Row {
            id: primaryRow

            spacing: surface._skin.spacing.xs

            CommandBar {
                id: primaryBar

                primaryCommands: surface.flyout._safePrimaryCommands
                secondaryCommands: []
                type: surface.flyout.type
                buttonStyle: Enums.commandBar.style_icon_only
                iconSize: surface.flyout.iconSize
                spacing: surface.flyout.spacing
                onActionTriggered: (index, action) =>
                    surface.flyout._triggerPrimary(index, action)
            }

            // Mini-expanded toggle: shows and hides the secondary command row
            // 迷你展开开关: 显示与隐藏次命令行
            Button {
                id: moreButton

                objectName: "commandBarFlyoutMoreButton"
                visible: surface._hasSecondary && !surface.flyout.alwaysExpanded
                style: surface._skin.button.style_transparent
                flat: true
                icon: surface._showSecondary
                    ? Enums.icon.chevron_up : Enums.icon.more_horizontal
                iconSize: surface.flyout.iconSize
                implicitWidth: surface._skin.controlSize.commandBarButtonSize
                implicitHeight: surface._skin.controlSize.commandBarButtonSize
                onClicked: surface.flyout.toggleSecondary()
            }
        }

        // Secondary commands: the mini-expanded panel 次命令: 迷你展开面板
        Row {
            id: secondaryRow

            spacing: surface._skin.spacing.xs
            visible: surface._showSecondary

            Repeater {
                model: surface.flyout._safeSecondaryCommands

                Button {
                    objectName: "commandBarFlyoutSecondaryAction" + index
                    style: surface._skin.button.style_transparent
                    flat: true
                    icon: modelData ? (modelData.icon || "") : ""
                    text: surface._secondaryText(modelData)
                    enabled: !modelData || modelData.enabled !== false
                    iconSize: surface.flyout.iconSize
                    onClicked: surface.flyout._triggerSecondary(index, modelData)
                }
            }

            // Full-expansion toggle: labels the secondary commands
            // 完全展开开关: 为次命令加标签
            Button {
                id: expandButton

                objectName: "commandBarFlyoutExpandButton"
                visible: !surface.flyout.alwaysExpanded
                style: surface._skin.button.style_transparent
                flat: true
                icon: surface.flyout.fullyExpanded
                    ? Enums.icon.chevron_up : Enums.icon.chevron_down
                iconSize: surface.flyout.iconSize
                implicitWidth: surface._skin.controlSize.commandBarButtonSize
                implicitHeight: surface._skin.controlSize.commandBarButtonSize
                onClicked: surface.flyout.toggleExpanded()
            }
        }
    }
}
