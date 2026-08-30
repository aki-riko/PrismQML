// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import ".."
import "../../data/Label"
import "../Card"
import "../../../effects"
import "../ScrollBar"
import "../../icons"
import QtQuick
import QtQuick.Effects

// TimelineVirtualRow - Virtualized timeline row delegate 虚拟时间线行委托
// Keeps the row branch separate from TimelineCore's data synchronization.
// 将行分支与 TimelineCore 的数据同步职责分离。
Item {
    id: rowDelegate

    // ==================== Required Props 必需属性 ====================
    required property var model

    // ==================== Internal Props 内部属性 ====================
    property Item headerPart: null
    property Item cardPart: null

    // ==================== Readonly State 只读状态 ====================
    readonly property var control: ListView.view ? ListView.view.timelineControl : null
    readonly property var listView: ListView.view
    readonly property Item activePart: model.kind === "header" ? headerPart : cardPart

    // ==================== Size 尺寸 ====================
    width: listView ? listView.width : 0
    height: activePart ? activePart.height : 0
    clip: !control._graphMode

    // Graph primitives stay inside each row and meet at the exact boundary.
    // 图元保持在行内并于边界精确拼接。
    TimelineGraphLayer {
        x: 0
        y: 0
        width: control._graphWidth
        height: rowDelegate.height
        visible: control._graphMode
        graphData: rowDelegate.model.graphData || {}
        showNode: rowDelegate.model.kind === "card"
        nodeY: rowDelegate.cardPart ? rowDelegate.cardPart.nodeY : 0
        opacity: control._pulseOpacity
        selected: showNode && !!rowDelegate.cardPart
            && rowDelegate.cardPart.isSelected
        graphPalette: control.graphPalette
    }

    // ==================== Content 内容 ====================
    // ---------- 组头行 ----------
    Repeater {
        model: rowDelegate.model.kind === "header" ? 1 : 0
        onItemAdded: (index, item) => rowDelegate.headerPart = item
        onItemRemoved: (index, item) => {
            if (rowDelegate.headerPart === item) rowDelegate.headerPart = null
        }

        delegate: Item {
            id: headerPart
            width: rowDelegate.width
            height: Enums.spacing.timelineHeaderHeight + Enums.spacing.s
            clip: true

            Row {
                anchors.left: parent.left
                anchors.leftMargin: control._graphMode ? control._graphWidth : 0
                anchors.verticalCenter: parent.verticalCenter
                spacing: Enums.spacing.m

                Rectangle {
                    objectName: "timelineStatusNode"
                    width: Enums.controlSize.timelineIcon
                    height: Enums.controlSize.timelineIcon
                    radius: Enums.controlSize.timelineIcon / 2
                    anchors.verticalCenter: parent.verticalCenter
                    color: control._getStatusColor(rowDelegate.model.status || "info")
                    visible: !control._graphMode
                    opacity: control._pulseOpacity

                    Icon {
                        anchors.centerIn: parent
                        icon: control._getStatusIcon(rowDelegate.model.status || "info")
                        iconSize: Enums.controlSize.timelineIconText
                        color: Enums.accentForeground
                    }
                }

                Label {
                    id: headerTitle
                    type: Enums.label.type_body_strong
                    anchors.verticalCenter: parent.verticalCenter
                    text: rowDelegate.model.title || ""
                }

                Rectangle {
                    visible: (rowDelegate.model.dateKey || "") !== ""
                        && rowDelegate.model.dateKey !== rowDelegate.model.title
                    width: headerDate.implicitWidth + Enums.spacing.m
                    height: headerDate.implicitHeight + Enums.spacing.xxs
                    radius: Enums.radius.small
                    color: Enums.stateColor.controlBgHover
                    border.width: Enums.border.thin
                    border.color: Enums.stateColor.borderLight

                    Label {
                        id: headerDate
                        anchors.centerIn: parent
                        type: Enums.label.type_caption
                        text: rowDelegate.model.dateKey || ""
                        color: Enums.textColor.secondary
                    }
                }
            }
        }
    }

    // ---------- 卡片行 ----------
    Repeater {
        model: rowDelegate.model.kind === "card" ? 1 : 0
        onItemAdded: (index, item) => rowDelegate.cardPart = item
        onItemRemoved: (index, item) => {
            if (rowDelegate.cardPart === item) rowDelegate.cardPart = null
        }

        delegate: Item {
            id: cardPart

            // ==================== Internal Props 内部属性 ====================
            readonly property int shadowPadding: Enums.spacing.cardShadow
            readonly property bool isSelected: control.selectedKey !== undefined
                && !!rowDelegate.model.cardData
                && (typeof rowDelegate.model.cardData === "object")
                && rowDelegate.model.cardData[control.selectedRole] === control.selectedKey
            readonly property string cardTime: rowDelegate.model.time || ""
            readonly property real nodeY: cardBox.y + cardBox.height / 2

            width: rowDelegate.width
            height: cardBox.y + cardBox.height + Enums.spacing.m
            clip: true

            // 左侧连接线
            Rectangle {
                objectName: "timelineStatusConnector"
                x: (Enums.controlSize.timelineIcon - width) / 2
                y: 0
                width: Enums.border.normal
                height: parent.height
                color: Enums.stateColor.borderSubtle
                visible: !control._graphMode
                opacity: Enums.opacityLevel.medium * control._pulseOpacity
            }

            Card {
                id: cardBox
                x: control._graphMode ? control._graphWidth : Enums.spacing.timelineIndent
                y: cardPart.shadowPadding
                // Keep the normal card inset; the viewport reserves the scrollbar gutter.
                // 保留常规卡片内缩；滚动条空间由视口统一预留。
                width: parent.width - x - Enums.spacing.m
                height: cardCol.implicitHeight + Enums.spacing.l * 2
                // Graph cards use Fluent elevation and the Card token border.
                // 图模式卡片使用 Fluent 层级动效与 Card 自带轻边框。
                cardType: control._graphMode
                    ? Enums.card.type_elevated : Enums.card.type_hover
                contentPadding: Enums.spacing.none
                clickEnabled: true

                onClicked: {
                    control.cardClicked(rowDelegate.model.groupIndex,
                        rowDelegate.model.cardIndex, rowDelegate.model.text)
                    control.cardClickedData(rowDelegate.model.groupIndex,
                        rowDelegate.model.cardIndex, rowDelegate.model.cardData)
                }

                // Fluent 左侧选中指示条(圆角 pill,accent 色,短竖条居中)
                Rectangle {
                    objectName: "timelineCardSelectionIndicator"
                    anchors.left: parent.left
                    anchors.leftMargin: Enums.spacing.xs
                    anchors.verticalCenter: parent.verticalCenter
                    width: Enums.border.thick
                    radius: Enums.radius.micro
                    color: Enums.accentColor
                    height: parent.height * 0.5
                    opacity: cardPart.isSelected ? 1 : 0
                    scale: cardPart.isSelected ? 1 : 0.7
                    transformOrigin: Item.Center

                    // Animator 在渲染线程推进；即使 GUI 线程正回填异步结果，
                    // 选中切换也不会停在半截。
                    Behavior on opacity {
                        OpacityAnimator { duration: Enums.duration.fast }
                    }
                    Behavior on scale {
                        ScaleAnimator {
                            duration: Enums.duration.fast
                            easing.type: Easing.OutCubic
                        }
                    }
                }

                Rectangle {
                    objectName: "timelineCardSelectionOutline"
                    anchors.fill: parent
                    radius: cardBox.borderRadius
                    color: Enums.transparent
                    border.width: Enums.border.normal
                    border.color: Enums.accentColor
                    opacity: cardPart.isSelected ? Enums.opacityLevel.visible : Enums.opacityLevel.invisible
                    Behavior on opacity {
                        OpacityAnimator { duration: Enums.duration.fast }
                    }
                }

                Column {
                    id: cardCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.margins: Enums.spacing.l
                    spacing: Enums.spacing.xxs

                    Row {
                        id: cardHeading
                        width: parent.width
                        spacing: Enums.spacing.s

                        Label {
                            id: cardTitle
                            type: Enums.label.type_body
                            width: cardTimeBadge.visible
                                ? Math.max(0, parent.width - cardTimeBadge.width - parent.spacing)
                                : parent.width
                            text: rowDelegate.model.text || ""
                            color: (rowDelegate.model.strikeOut || false)
                                ? Enums.textColor.secondary : Enums.textColor.primary
                            wrapMode: Text.Wrap
                            font.strikeout: rowDelegate.model.strikeOut || false
                        }

                        Rectangle {
                            id: cardTimeBadge
                            objectName: "timelineCardTimeBadge"
                            visible: cardPart.cardTime !== ""
                            width: timeLabel.implicitWidth + Enums.spacing.m
                            height: timeLabel.implicitHeight + Enums.spacing.xxs
                            radius: Enums.radius.small
                            color: Enums.stateColor.controlBgHover
                            border.width: Enums.border.thin
                            border.color: Enums.accentColor

                            Label {
                                id: timeLabel
                                anchors.centerIn: parent
                                type: Enums.label.type_caption
                                text: cardPart.cardTime
                                color: Enums.accentColor
                            }
                        }
                    }

                    TimelineGraphLabels {
                        width: parent.width
                        visible: control._graphMode
                            && !!rowDelegate.model.cardData
                            && !!rowDelegate.model.cardData.labels
                            && rowDelegate.model.cardData.labels.length > 0
                        labels: visible ? rowDelegate.model.cardData.labels : []
                    }
                    Label {
                        type: Enums.label.type_caption
                        width: parent.width
                        visible: (rowDelegate.model.description || "") !== ""
                        text: rowDelegate.model.description || ""
                        color: Enums.textColor.tertiary
                        wrapMode: Text.Wrap
                    }
                }
            }
        }
    }
}
