// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import ".."
import "../../data/Label"
import "../Card"
import "../../icons"
import QtQuick

// TimelineStandardContent - Full timeline content 全量时间线内容
// Keeps the non-virtual branch separate from TimelineCore's flat model sync.
// 将非虚拟分支与 TimelineCore 的拍平模型同步职责分离。
Column {
    id: contentColumn

    // ==================== Required Props 必需属性 ====================
    required property var timeline

    // ==================== Size 尺寸 ====================
    width: timeline ? timeline.width : 0
    spacing: Enums.spacing.none
    visible: !timeline._usesVirtualList

    // ==================== Content 内容 ====================
    Repeater {
        model: timeline._usesVirtualList ? [] : timeline._safeItems

        delegate: Item {
            id: groupItem

            required property var modelData
            required property int index
            readonly property var groupData: modelData || ({})

            width: contentColumn.width
            height: groupContent.height

            // Connector line 连接线（在图标下方）
            Rectangle {
                x: 7
                y: Enums.spacing.timelineHeaderHeight
                width: Enums.border.normal
                height: parent.height - Enums.spacing.timelineHeaderHeight
                color: Enums.stateColor.borderSubtle
            }

            Column {
                id: groupContent
                width: parent.width
                spacing: Enums.spacing.none

                // Group header 分组标题
                Item {
                    width: groupContent.width
                    height: Enums.spacing.timelineHeaderHeight

                    Row {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: Enums.spacing.m

                        // Status icon 状态图标（圆形填充）
                        Rectangle {
                            width: Enums.controlSize.timelineIcon
                            height: Enums.controlSize.timelineIcon
                            radius: Enums.controlSize.timelineIcon / 2
                            anchors.verticalCenter: parent.verticalCenter
                            color: timeline._getStatusColor(
                                groupItem.groupData.status || "info"
                            )

                            Icon {
                                anchors.centerIn: parent
                                icon: timeline._getStatusIcon(
                                    groupItem.groupData.status || "info"
                                )
                                iconSize: Enums.controlSize.timelineIconText
                                color: Enums.accentForeground
                            }
                        }

                        // Title 标题
                        Label {
                            type: Enums.label.type_body_strong
                            anchors.verticalCenter: parent.verticalCenter
                            text: groupItem.groupData.title || ""
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: timeline.itemClicked(
                            groupItem.index, groupItem.groupData.title || ""
                        )
                    }
                }

                // Cards container 卡片容器
                Column {
                    width: groupContent.width
                    spacing: Enums.spacing.m
                    leftPadding: Enums.spacing.timelineIndent
                    topPadding: Enums.spacing.s
                    bottomPadding: Enums.spacing.l

                    Repeater {
                        model: groupItem.groupData.cards || []

                        delegate: Item {
                            id: cardItem

                            required property var modelData
                            required property int index
                            readonly property var cardData: modelData || ""

                            // Card status 卡片状态
                            property string cardStatus: cardData
                                && typeof cardData === "object"
                                ? (cardData.status || groupItem.groupData.status || "info")
                                : (groupItem.groupData.status || "info")
                            property bool hasStrikeOut: cardData
                                && typeof cardData === "object"
                                ? (cardData.strikeOut || false) : false
                            property string cardText: typeof cardData === "string"
                                ? cardData : (cardData ? (cardData.text || "") : "")
                            property string cardDescription: cardData
                                && typeof cardData === "object"
                                ? (cardData.description || "") : ""

                            width: groupContent.width - 56
                            height: simpleCard.height

                            Card {
                                id: simpleCard
                                cardType: Enums.card.type_hover
                                contentPadding: Enums.spacing.none
                                width: parent.width
                                height: cardContent.implicitHeight + Enums.spacing.l * 2
                                clickEnabled: true
                                onClicked: {
                                    timeline.cardClicked(
                                        groupItem.index, cardItem.index, cardItem.cardText
                                    )
                                    timeline.cardClickedData(
                                        groupItem.index, cardItem.index, cardItem.modelData
                                    )
                                }

                                Row {
                                    id: cardContent
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.margins: Enums.spacing.l
                                    spacing: Enums.spacing.m

                                    // Card status icon 卡片状态图标
                                    Rectangle {
                                        width: Enums.controlSize.timelineCardIcon
                                        height: Enums.controlSize.timelineCardIcon
                                        radius: Enums.radius.medium
                                        anchors.verticalCenter: parent.verticalCenter
                                        color: timeline._getStatusColor(cardItem.cardStatus)

                                        Icon {
                                            anchors.centerIn: parent
                                            icon: timeline._getStatusIcon(cardItem.cardStatus)
                                            iconSize: Enums.controlSize.timelineCardIconText
                                            color: Enums.accentForeground
                                        }
                                    }

                                    // Card text 卡片文字（主标题 + 可选副标题）
                                    Column {
                                        width: parent.width - 24
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: Enums.spacing.xxs

                                        Label {
                                            type: Enums.label.type_body
                                            width: parent.width
                                            text: cardItem.cardText
                                            color: cardItem.hasStrikeOut
                                                ? Enums.textColor.secondary
                                                : Enums.textColor.primary
                                            wrapMode: Text.Wrap
                                            font.strikeout: cardItem.hasStrikeOut
                                        }
                                        Label {
                                            type: Enums.label.type_caption
                                            width: parent.width
                                            visible: cardItem.cardDescription !== ""
                                            text: cardItem.cardDescription
                                            color: Enums.textColor.tertiary
                                            wrapMode: Text.Wrap
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
