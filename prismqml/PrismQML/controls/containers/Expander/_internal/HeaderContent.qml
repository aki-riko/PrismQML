// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../icons"
import "../../../data/Label"

// HeaderContent - Expander header visuals and interaction 展开器头部视觉与交互
// Keeps header layout separate while ExpanderCore owns state and content.
// 将头部布局独立出来，同时由 ExpanderCore 持有状态与内容。
Item {
    id: headerRoot

    // ==================== Required Props 必需属性 ====================
    required property var expanderControl

    // ==================== Public Props 公开属性 ====================
    property alias title: titleLabel.text
    property alias content: contentLabel.text
    property alias headerContent: headerContentLoader.sourceComponent
    property alias titleLabel: titleLabel
    property alias contentLabel: contentLabel
    property alias headerContentLoader: headerContentLoader

    // ==================== Readonly State 只读状态 ====================
    readonly property bool hovered: !expanderControl.disabled
        && headerArea.containsMouse
    readonly property bool pressed: !expanderControl.disabled
        && headerArea.pressed

    // ==================== Size 尺寸 ====================
    anchors.top: parent.top
    anchors.left: parent.left
    anchors.right: parent.right
    height: contentLabel.text !== "" ? 72 : 48

    // ==================== Content 内容 ====================
    Row {
        id: headerRow

        anchors.fill: parent
        anchors.leftMargin: Enums.spacing.xl
        anchors.rightMargin: Enums.spacing.xl
        spacing: Enums.spacing.none
        z: Enums.zIndex.content

        // Icon 图标
        Item {
            width: expanderControl.icon !== ""
                ? (Enums.iconSize.m + Enums.spacing.xl) : 0
            height: parent.height
            visible: expanderControl.icon !== ""

            Icon {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                iconSize: Enums.iconSize.m
                icon: expanderControl.icon
                color: Enums.textColor.primary
            }
        }

        // Title and content 标题和内容
        Column {
            id: titleCol

            anchors.verticalCenter: parent.verticalCenter
            spacing: Enums.spacing.none

            Label {
                id: titleLabel

                type: expanderControl.titleType
            }

            Label {
                id: contentLabel

                type: Enums.label.type_caption
                color: Enums.stateColor.settingCardContent
                visible: text !== ""
            }
        }

        // Spacer 弹性空间
        Item {
            width: Math.max(
                1,
                headerRoot.width - Enums.spacing.xl - Enums.spacing.m
                - (expanderControl.icon !== ""
                    ? (Enums.iconSize.m + Enums.spacing.xl) : 0)
                - titleCol.implicitWidth - headerContentLoader.width
                - Enums.controlSize.expanderIconSize
                - (headerContentLoader.item ? Enums.spacing.xl : 0)
            )
            height: Enums.border.thin
        }

        // Header content loader 头部内容加载器
        Loader {
            id: headerContentLoader

            anchors.verticalCenter: parent.verticalCenter
        }

        // Spacing between header content and expand button 头部内容与展开按钮之间的间距
        Item {
            width: headerContentLoader.item ? Enums.spacing.xl : 0
            height: Enums.border.thin
            visible: headerContentLoader.item
        }

        // Expand button 展开按钮 (Fluent Design: 30x30)
        Item {
            width: Enums.controlSize.expanderIconSize
            height: Enums.controlSize.expanderIconSize
            anchors.verticalCenter: parent.verticalCenter

            Rectangle {
                anchors.fill: parent
                radius: Enums.surfaceRadius(Enums.radius.small)
                color: {
                    if (headerRoot.pressed) return Enums.stateColor.expandBtnPressed
                    if (headerRoot.hovered) return Enums.stateColor.expandBtnHover
                    return Enums.transparent
                }
            }

            // Arrow icon with rotation 带旋转的箭头图标
            Icon {
                anchors.centerIn: parent
                iconSize: Enums.iconSize.tiny
                icon: Enums.icon.chevron_down
                color: Enums.textColor.secondary
                rotation: expanderControl.expanded ? 180 : 0

                Behavior on rotation {
                    NumberAnimation {
                        duration: Enums.duration.medium
                        easing.type: Easing.OutQuad
                    }
                }
            }
        }
    }

    // Click handler 点击处理
    MouseArea {
        id: headerArea

        anchors.fill: parent
        hoverEnabled: true
        enabled: !expanderControl.disabled
        onClicked: {
            expanderControl.expanded = !expanderControl.expanded
            expanderControl.toggled(expanderControl.expanded)
        }
    }
}
