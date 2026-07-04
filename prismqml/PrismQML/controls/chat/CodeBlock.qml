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
    readonly property int _radius: Enums.isPrismDesign ? Enums.prismDesign.radiusCard : Enums.radius.small
    readonly property color _blockBackground: Enums.isPrismDesign ? Enums.dialogColor : "#1E1E1E"
    readonly property color _blockBorder: Enums.isPrismDesign ? Enums.borderColor : Qt.rgba(1, 1, 1, 0.08)
    readonly property color _mutedText: Enums.isPrismDesign ? Enums.textColor.secondary : "#9CA3AF"
    readonly property color _codeText: Enums.isPrismDesign ? Enums.textColor.primary : "#E5E7EB"
    readonly property color _copyHover: Enums.isPrismDesign ? Enums.hoverColor : Qt.rgba(1, 1, 1, 0.1)

    color: _blockBackground
    radius: _radius
    border.color: _blockBorder
    border.width: Enums.border.thin

    implicitWidth: 400
    implicitHeight: codeText.implicitHeight + headerRow.height + 16

    Item {
        id: headerRow
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 8
        height: 24

        Text {
            id: langLabel
            text: control.language
            color: control._mutedText
            font.family: Enums.fontFamily
            font.pixelSize: 11
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            visible: control.language !== ""
        }

        MouseArea {
            id: copyBtn
            width: 50
            height: 22
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            cursorShape: Qt.PointingHandCursor
            hoverEnabled: true

            Rectangle {
                anchors.fill: parent
                radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small
                color: copyBtn.containsMouse ? control._copyHover : Enums.transparent

                Text {
                    anchors.centerIn: parent
                    text: copyBtn._copied ? "已复制" : "复制"
                    color: copyBtn._copied ? Enums.statusLevel.successColor : control._mutedText
                    font.family: Enums.fontFamily
                    font.pixelSize: 11
                }
            }

            property bool _copied: false
            Timer {
                id: copiedTimer
                interval: 1500
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
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        anchors.bottomMargin: 8
        anchors.topMargin: 4

        text: control.code
        color: control._codeText
        font.family: "Consolas, 'Courier New', monospace"
        font.pixelSize: 12
        wrapMode: Text.Wrap
        textFormat: Text.PlainText
    }
}
