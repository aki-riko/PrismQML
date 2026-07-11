// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

/**
 * CodeBlock — 代码块组件
 *
 * 黑底等宽字体显示一段代码,右上角带"复制"按钮。
 * 可选 language 标签显示在左上角。
 *
 * Props:
 *   code: string         代码内容
 *   language: string     语言标签 (可选)
 */
Rectangle {
    id: control

    property string code: ""
    property string language: ""

    color: Enums.codeBlockColors.background
    radius: Enums.radius.small
    border.color: Enums.codeBlockColors.border
    border.width: Enums.border.thin

    implicitWidth: Enums.controlSize.codeBlockDefaultWidth
    implicitHeight: codeText.implicitHeight + headerRow.height + Enums.spacing.xl

    Item {
        id: headerRow
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: Enums.spacing.m
        height: Enums.controlSize.codeBlockHeaderHeight

        Text {
            id: langLabel
            text: control.language
            color: Enums.codeBlockColors.secondaryText
            font.family: Enums.fontFamily
            font.pixelSize: Enums.typography.captionCompact
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            visible: control.language !== ""
        }

        MouseArea {
            id: copyBtn
            width: Enums.controlSize.codeBlockCopyButtonWidth
            height: Enums.controlSize.codeBlockCopyButtonHeight
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            cursorShape: Qt.PointingHandCursor
            hoverEnabled: true

            Rectangle {
                anchors.fill: parent
                radius: Enums.radius.small
                color: copyBtn.containsMouse ? Enums.codeBlockColors.hover : Enums.transparent

                Text {
                    anchors.centerIn: parent
                    text: copyBtn._copied ? "已复制" : "复制"
                    color: copyBtn._copied ? Enums.codeBlockColors.copySuccess : Enums.codeBlockColors.secondaryText
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.captionCompact
                }
            }

            property bool _copied: false
            Timer {
                id: copiedTimer
                interval: Enums.duration.copyFeedback
                onTriggered: copyBtn._copied = false
            }

            onClicked: {
                _clipboardHelper.text = control.code
                _clipboardHelper.selectAll()
                _clipboardHelper.copy()
                _copied = true
                copiedTimer.restart()
            }
        }
    }

    // 隐藏的 TextEdit 用于走 clipboard.copy()
    TextEdit {
        id: _clipboardHelper
        visible: false
        width: 0; height: 0
    }

    Text {
        id: codeText
        anchors.top: headerRow.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: Enums.spacing.l
        anchors.rightMargin: Enums.spacing.l
        anchors.bottomMargin: Enums.spacing.m
        anchors.topMargin: Enums.spacing.xs

        text: control.code
        color: Enums.codeBlockColors.foreground
        font.family: Enums.fontMonospace
        font.pixelSize: Enums.typography.caption
        wrapMode: Text.Wrap
        textFormat: Text.PlainText
    }
}
