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

    // ==================== Public Props 公开属性 ====================
    property string code: ""
    property string language: ""

    // ==================== Internal Props 内部属性 ====================
    readonly property int _radius: Enums.isPrismDesign ? Enums.prismDesign.radiusCard : Enums.radius.small
    readonly property color _blockBackground: Enums.isPrismDesign ? Enums.dialogColor : "#1E1E1E"
    readonly property color _blockBorder: Enums.isPrismDesign ? Enums.borderColor : Qt.rgba(1, 1, 1, 0.08)
    readonly property int _blockBorderWidth: Enums.isPrismDesign ? Enums.prismDesign.borderWidth : Enums.border.thin
    readonly property color _mutedText: Enums.isPrismDesign ? Enums.textColor.secondary : "#9CA3AF"
    readonly property color _codeText: Enums.isPrismDesign ? Enums.textColor.primary : "#E5E7EB"
    readonly property color _copyHover: Enums.isPrismDesign ? Enums.hoverColor : Qt.rgba(1, 1, 1, 0.1)
    readonly property int _copyRadius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small
    readonly property color _copyTextColor: _mutedText
    readonly property color _copySuccessTextColor: Enums.statusLevel.successColor
    readonly property int _labelFontSize: Enums.typography.caption
    readonly property int _codeFontSize: Enums.typography.caption

    // ==================== Size 尺寸 ====================
    color: _blockBackground
    radius: _radius
    border.color: _blockBorder
    border.width: _blockBorderWidth

    implicitWidth: 400
    implicitHeight: codeText.implicitHeight + headerRow.height + Enums.spacing.xl

    // ==================== Content 内容 ====================
    Item {
        id: headerRow
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: Enums.spacing.m
        height: Enums.controlSize.buttonHeight - Enums.spacing.l

        Text {
            id: langLabel
            text: control.language
            color: control._mutedText
            font.family: Enums.fontFamily
            font.pixelSize: control._labelFontSize
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            visible: control.language !== ""
        }

        MouseArea {
            id: copyBtn

            property bool _copied: false

            width: 50
            height: 22
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            cursorShape: Qt.PointingHandCursor
            hoverEnabled: true

            Rectangle {
                anchors.fill: parent
                radius: control._copyRadius
                color: copyBtn.containsMouse ? control._copyHover : Enums.transparent

                Text {
                    anchors.centerIn: parent
                    text: copyBtn._copied ? "已复制" : "复制"
                    color: copyBtn._copied ? control._copySuccessTextColor : control._copyTextColor
                    font.family: Enums.fontFamily
                    font.pixelSize: control._labelFontSize
                }
            }

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
        font.pixelSize: control._codeFontSize
        wrapMode: Text.Wrap
        textFormat: Text.PlainText
    }
}
