// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../.."
import "."

/**
 * MarkdownView - Lightweight Markdown renderer 简易 Markdown 渲染器
 *
 * Splits Markdown into paragraphs and fenced code blocks: 将 Markdown 拆分为段落和围栏代码块：
 *   - Fenced block ```lang\n...\n``` -> CodeBlock 围栏代码块映射到 CodeBlock
 *   - Other text -> Text.MarkdownText 其他文本交由 Text.MarkdownText 渲染
 *
 * Props 公开属性:
 *   markdown: string  Raw Markdown text 原始 Markdown 文本
 *   textColor: color  Body text color 正文颜色
 *   linkColor: color  Link color 链接颜色
 */
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string markdown: ""
    property color textColor: Enums.textColor.primary
    property color linkColor: Enums.accentColor

    // ==================== Readonly State 只读状态 ====================
    // Parse Markdown into text and fenced-code blocks 将 Markdown 解析为文本块和围栏代码块
    readonly property var _blocks: _parseBlocks(markdown)

    // ==================== Internal Methods 内部方法 ====================
    function _parseBlocks(md) {
        if (!md) return []
        var blocks = []
        var lines = md.split('\n')
        var inCode = false
        var codeLang = ""
        var codeBuf = []
        var textBuf = []

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i]
            var fenceMatch = line.match(/^```(\w*)\s*$/)
            if (fenceMatch) {
                if (!inCode) {
                    if (textBuf.length > 0) {
                        blocks.push({ kind: "text", content: textBuf.join('\n') })
                        textBuf = []
                    }
                    inCode = true
                    codeLang = fenceMatch[1] || ""
                    codeBuf = []
                } else {
                    blocks.push({ kind: "code", language: codeLang, content: codeBuf.join('\n') })
                    inCode = false
                    codeLang = ""
                    codeBuf = []
                }
            } else if (inCode) {
                codeBuf.push(line)
            } else {
                textBuf.push(line)
            }
        }

        // Flush buffered content 刷新缓冲内容
        if (inCode && codeBuf.length > 0) {
            blocks.push({ kind: "code", language: codeLang, content: codeBuf.join('\n') })
        }
        if (textBuf.length > 0) {
            blocks.push({ kind: "text", content: textBuf.join('\n') })
        }

        return blocks
    }

    implicitHeight: contentColumn.implicitHeight
    implicitWidth: parent ? parent.width : Enums.controlSize.chatContentMaxWidth

    // ==================== Content 内容 ====================
    ColumnLayout {
        id: contentColumn
        width: parent.width
        spacing: Enums.spacing.m

        Repeater {
            model: control._blocks

            delegate: Loader {
                required property var modelData

                Layout.fillWidth: true
                sourceComponent: modelData.kind === "code" ? codeCmp : textCmp

                Component {
                    id: textCmp
                    Text {
                        // Qt CommonMark handles lists, emphasis, headings, inline code, links,
                        // and paragraph breaks, replacing the old subset regex parser
                        // Qt CommonMark 处理列表、强调、标题、行内码、链接和段落换行，替代旧子集正则解析器
                        text: modelData.content
                        color: control.textColor
                        linkColor: control.linkColor
                        textFormat: Text.MarkdownText
                        wrapMode: Text.WordWrap
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.body
                        onLinkActivated: (url) => Qt.openUrlExternally(url)
                    }
                }
                Component {
                    id: codeCmp
                    CodeBlock {
                        code: modelData.content
                        language: modelData.language
                    }
                }
            }
        }
    }
}
