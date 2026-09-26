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
    // Wrap long header text instead of overflowing the header row 长标题改为换行而非撑破头部
    // 关闭时保持单行省略的历史行为 关闭时保持单行省略的历史行为
    property bool wrapHeaderText: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool hovered: !expanderControl.disabled
        && headerArea.containsMouse
    readonly property bool pressed: !expanderControl.disabled
        && headerArea.pressed
    // Touch has no hover preview: on touch the hover treatment follows the press
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
    readonly property bool _touchActive: Touch.feedback(hovered, pressed)
    // Width taken by the expand button, its gap and the icon column
    // 展开按钮、其与文本之间的间距以及图标列占用的宽度
    readonly property real _trailingWidth: Enums.controlSize.expanderIconSize
        + (expanderControl.icon !== ""
            ? (Enums.iconSize.m + Enums.spacing.xl) : 0)
        + (headerContentLoader.item ? Enums.spacing.xl : 0)
        + Enums.spacing.m
    // Inner width left for the title column 标题列可用的内部宽度
    readonly property real _availableTextWidth: Math.max(0,
        headerRoot.width - Enums.spacing.xl * 2 - _trailingWidth
        - headerContentLoader.width)
    // Text block height, always reserved from the typography line box
    // 文本块高度: 始终按字体行高预留, 只有换行时才会因多行而变高
    readonly property real _textBlockHeight: titleLabel.implicitHeight
        + (contentLabel.text !== "" ? contentLabel.implicitHeight : 0)
    readonly property real _minHeaderHeight: 48

    // ==================== Size 尺寸 ====================
    anchors.top: parent.top
    anchors.left: parent.left
    anchors.right: parent.right
    // 两行文本时保持 72 的历史高度; 换行超出后按实际行高自适应
    height: Math.max(_minHeaderHeight,
                     contentLabel.text !== "" ? Math.max(72, _textBlockHeight)
                                              : Math.max(48, _textBlockHeight))

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
            // Never let long header text push the expand button out of the header.
            // Deliberately independent of titleCol.implicitWidth to avoid a width loop
            // 绝不让长文本把展开按钮挤出头部区域; 刻意不依赖自身 implicitWidth 以免宽度循环
            width: headerRoot._availableTextWidth

            Label {
                id: titleLabel

                type: Enums.label.type_body_strong
                objectName: "expanderHeaderTitle"
                // Explicit width: plain Column does not propagate its width to children,
                // and it must not read titleCol.implicitWidth (that would be a width loop)
                // 显式设宽: 普通 Column 不会把宽度传给子项, 且不能读 titleCol.implicitWidth
                // (那会形成宽度循环)
                width: Math.min(implicitWidth, titleCol.width)
                wrapMode: headerRoot.wrapHeaderText ? Text.WordWrap : Text.NoWrap
                elide: headerRoot.wrapHeaderText ? Text.ElideNone : Text.ElideRight
            }

            Label {
                id: contentLabel

                type: Enums.label.type_caption
                color: Enums.stateColor.settingCardContent
                objectName: "expanderHeaderContent"
                visible: text !== ""
                width: Math.min(implicitWidth, titleCol.width)
                wrapMode: headerRoot.wrapHeaderText ? Text.WordWrap : Text.NoWrap
                elide: headerRoot.wrapHeaderText ? Text.ElideNone : Text.ElideRight
            }
        }

        // Spacer 弹性空间
        Item {
            width: Math.max(
                1,
                headerRoot.width - Enums.spacing.xl - Enums.spacing.m
                - (expanderControl.icon !== ""
                    ? (Enums.iconSize.m + Enums.spacing.xl) : 0)
                - titleCol.width - headerContentLoader.width
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
                    if (headerRoot._touchActive) return Enums.stateColor.expandBtnHover
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
