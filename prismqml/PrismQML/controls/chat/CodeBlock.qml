// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal" as ChatInternal

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
    readonly property int _radius: Enums.radius.small
    readonly property color _blockBackground: Enums.codeBlockColors.background
    readonly property color _blockBorder: Enums.codeBlockColors.border
    readonly property real _blockBorderWidth: Enums.border.thin
    readonly property color _mutedText: Enums.codeBlockColors.secondaryText
    readonly property color _codeText: Enums.codeBlockColors.foreground
    readonly property color _copyHover: Enums.codeBlockColors.hover
    readonly property int _copyRadius: Enums.radius.small
    readonly property color _copyTextColor: _mutedText
    readonly property color _copySuccessTextColor: Enums.codeBlockColors.copySuccess
    readonly property int _labelFontSize: Enums.typography.captionCompact
    readonly property int _codeFontSize: Enums.typography.caption
    readonly property string _codeFontFamily: Enums.fontMonospace
    readonly property int _headerHeight: Enums.controlSize.codeBlockHeaderHeight

    // ==================== Size 尺寸 ====================
    color: _blockBackground
    radius: _radius
    border.color: _blockBorder
    border.width: _blockBorderWidth

    implicitWidth: Enums.controlSize.codeBlockDefaultWidth
    implicitHeight: codeText.implicitHeight + headerRow.height + Enums.spacing.xl

    // ==================== Content 内容 ====================
    Item {
        id: headerRow
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: Enums.spacing.m
        height: control._headerHeight

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

            width: Enums.controlSize.codeBlockCopyButtonWidth
            height: Enums.controlSize.codeBlockCopyButtonHeight
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            cursorShape: Qt.PointingHandCursor
            hoverEnabled: true

            onClicked: {
                clipboardLoader.active = true
                var helper = clipboardLoader.item
                if (!helper) {
                    console.warn("CodeBlock: clipboard helper failed to load")
                    return
                }
                helper.text = control.code
                helper.selectAll()
                helper.copy()
                clipboardLoader.active = false
                _copied = true
                copiedTimer.restart()
            }

            Rectangle {
                anchors.fill: parent
                radius: control._copyRadius
                color: copyBtn.containsMouse ? control._copyHover : Enums.transparent

                Text {
                    anchors.centerIn: parent
                    text: {
                        Translator._v
                        return copyBtn._copied
                            ? Translator.tr("copied")
                            : Translator.tr("copy")
                    }
                    color: copyBtn._copied ? control._copySuccessTextColor : control._copyTextColor
                    font.family: Enums.fontFamily
                    font.pixelSize: control._labelFontSize
                }
            }

            ChatInternal.CodeBlockCopyFeedbackTimer {
                id: copiedTimer
                host: copyBtn
            }
        }
    }

    // Create the clipboard TextEdit only during copy. 仅在复制时创建剪贴板 TextEdit。
    Loader {
        id: clipboardLoader

        active: false
        source: "_internal/CodeBlockClipboard.qml"
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
        color: control._codeText
        font.family: control._codeFontFamily
        font.pixelSize: control._codeFontSize
        wrapMode: Text.Wrap
        textFormat: Text.PlainText
    }
}
