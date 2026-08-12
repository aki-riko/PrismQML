// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import PrismQML

// Vintage ticket preview - Real component specimen 复古票据预览 - 真实组件样张
Window {
    id: root

    readonly property int pageMargin: Enums.spacing.xxl
    readonly property int ticketPadding: Enums.spacing.xxxl
    readonly property int ticketWidth: 1120
    readonly property int ticketHeight: 700
    readonly property int stubWidth: 220
    readonly property int perforationDashHeight: Enums.spacing.m
    readonly property int perforationGap: Enums.spacing.s
    readonly property int routeColumnWidth: 210
    readonly property int progressWidth: 430
    readonly property int journeyProgress: 62

    width: ticketWidth + pageMargin * 2
    height: ticketHeight + pageMargin * 2
    minimumWidth: width
    minimumHeight: height
    visible: true
    title: "PrismQML - Vintage Ticket Preview"
    color: Enums.backgroundColor

    Rectangle {
        id: ticket

        anchors.fill: parent
        anchors.margins: root.pageMargin
        radius: Enums.ticket.radius
        color: Enums.cardColor
        border.width: Enums.ticket.borderWidth
        border.color: Enums.borderColor
        clip: true

        TicketPaper {
            anchors.fill: parent
        }

        // Main ticket title 主票标题
        Column {
            id: titleBlock

            anchors.left: parent.left
            anchors.top: parent.top
            anchors.leftMargin: root.ticketPadding
            anchors.topMargin: root.ticketPadding
            spacing: Enums.spacing.xs

            Label {
                type: Enums.label.type_title
                text: "PRISMQML RAILWAY BUREAU"
                color: Enums.foregroundColor
                font.bold: true
                font.letterSpacing: Enums.spacing.xxs
            }

            Label {
                type: Enums.label.type_caption
                text: "LIMITED EXPRESS / UI COMPONENT SPECIMEN"
                color: Enums.secondaryForeground
            }
        }

        Label {
            anchors.right: perforation.left
            anchors.top: parent.top
            anchors.rightMargin: root.ticketPadding
            anchors.topMargin: root.ticketPadding
            type: Enums.label.type_caption
            text: "SERIAL VT-0000344"
            color: Enums.ticket.danger
            font.bold: true
        }

        Separator {
            anchors.left: parent.left
            anchors.right: perforation.left
            anchors.top: titleBlock.bottom
            anchors.leftMargin: root.ticketPadding
            anchors.rightMargin: root.ticketPadding
            anchors.topMargin: Enums.spacing.l
            lineColor: Enums.ticket.dividerColor
        }

        // Route fields 路线字段
        Row {
            id: routeRow

            anchors.left: parent.left
            anchors.right: perforation.left
            anchors.top: titleBlock.bottom
            anchors.leftMargin: root.ticketPadding
            anchors.rightMargin: root.ticketPadding
            anchors.topMargin: Enums.spacing.xxxl
            spacing: Enums.spacing.xxxl

            Column {
                width: root.routeColumnWidth
                spacing: Enums.spacing.xs

                Label { type: Enums.label.type_caption; text: "FROM / 始发"; color: Enums.secondaryForeground }
                Label { type: Enums.label.type_title; text: "PAPER TERMINAL"; color: Enums.foregroundColor; font.bold: true }
                Tag { text: "GATE 04"; status: Enums.statusLevel.success; showBorder: true }
            }

            Column {
                width: root.routeColumnWidth
                spacing: Enums.spacing.xs

                Label { type: Enums.label.type_caption; text: "TO / 到达"; color: Enums.secondaryForeground }
                Label { type: Enums.label.type_title; text: "INK CENTRAL"; color: Enums.foregroundColor; font.bold: true }
                Tag { text: "PLATFORM 02"; status: Enums.statusLevel.warning; showBorder: true }
            }

            Column {
                width: 180
                spacing: Enums.spacing.xs

                Label { type: Enums.label.type_caption; text: "DEPARTURE / 发车"; color: Enums.secondaryForeground }
                Label { type: Enums.label.type_title; text: "08:26"; color: Enums.ticket.danger; font.bold: true }
                Label { type: Enums.label.type_caption; text: "12 AUG 2026"; color: Enums.foregroundColor }
            }
        }

        // Interactive specimen 交互控件样张
        Column {
            id: controlsBlock

            anchors.left: parent.left
            anchors.right: perforation.left
            anchors.top: routeRow.bottom
            anchors.leftMargin: root.ticketPadding
            anchors.rightMargin: root.ticketPadding
            anchors.topMargin: Enums.spacing.xxl
            spacing: Enums.spacing.l

            Row {
                spacing: Enums.spacing.l

                LineEdit {
                    width: 250
                    placeholderText: "PASSENGER NAME"
                    text: "AKI RIKO"
                }

                ComboBoxDefault {
                    width: 220
                    model: ["FIRST CLASS", "STANDARD", "SLEEPER"]
                    currentIndex: 0
                }

                Button {
                    text: "VALIDATE"
                    style: Enums.button.style_primary
                    icon: Enums.icon.ticket_horizontal
                }
            }

            Row {
                spacing: Enums.spacing.xl

                CheckBox { text: "BAGGAGE"; checked: true }
                RadioButton { text: "ONE WAY"; checked: true }
                ToggleSwitch { text: "BOARDING"; checked: true }
                Chip { text: "ADMIT ONE"; checked: true; closable: false }
                Badge { count: 4; level: Enums.statusLevel.error }
            }

            Slider {
                width: root.progressWidth
                value: root.journeyProgress
                suffix: "%"
            }

            ProgressBar {
                width: root.progressWidth
                value: root.journeyProgress
            }

            InfoBar {
                width: 720
                severity: "success"
                title: "TICKET VALIDATED"
                message: "Coach B / Seat 12A / Gate closes 08:20"
                duration: 0
            }
        }

        // Perforation 撕票虚线
        Item {
            id: perforation

            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: stub.left
            width: Enums.border.thin

            Column {
                anchors.centerIn: parent
                spacing: root.perforationGap

                Repeater {
                    model: Math.floor(
                        (root.ticketHeight - root.ticketPadding * 2)
                        / (root.perforationDashHeight + root.perforationGap)
                    )

                    Rectangle {
                        width: Enums.border.thin
                        height: root.perforationDashHeight
                        color: Enums.ticket.dividerColor
                    }
                }
            }
        }

        // Detachable stub 副券
        Rectangle {
            id: stub

            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            width: root.stubWidth
            color: Enums.transparent

            Column {
                anchors.centerIn: parent
                width: parent.width - root.ticketPadding
                spacing: Enums.spacing.l

                Label {
                    anchors.horizontalCenter: parent.horizontalCenter
                    type: Enums.label.type_title
                    text: "ADMIT ONE"
                    color: Enums.foregroundColor
                    font.bold: true
                }

                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 150
                    height: 150
                    radius: width / 2
                    color: Enums.transparent
                    border.width: Enums.ticket.borderWidth
                    border.color: Enums.ticket.success
                    rotation: -12

                    Column {
                        anchors.centerIn: parent
                        spacing: Enums.spacing.xs

                        Label { anchors.horizontalCenter: parent.horizontalCenter; type: Enums.label.type_caption; text: "INSPECTED"; color: Enums.ticket.success; font.bold: true }
                        Label { anchors.horizontalCenter: parent.horizontalCenter; type: Enums.label.type_title; text: "08:12"; color: Enums.ticket.success; font.bold: true }
                        Label { anchors.horizontalCenter: parent.horizontalCenter; type: Enums.label.type_caption; text: "GATE 04"; color: Enums.ticket.success }
                    }
                }

                Separator { width: parent.width; lineColor: Enums.ticket.dividerColor }

                Label { type: Enums.label.type_caption; text: "COACH / 车厢"; color: Enums.secondaryForeground }
                Label { type: Enums.label.type_title; text: "B"; color: Enums.foregroundColor; font.bold: true }
                Label { type: Enums.label.type_caption; text: "SEAT / 座位"; color: Enums.secondaryForeground }
                Label { type: Enums.label.type_title; text: "12A"; color: Enums.ticket.danger; font.bold: true }
                Label { type: Enums.label.type_caption; text: "NON-TRANSFERABLE"; color: Enums.secondaryForeground }
            }
        }
    }
}
