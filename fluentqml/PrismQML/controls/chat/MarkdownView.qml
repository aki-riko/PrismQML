// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../.."
import "."

/**
 * MarkdownView — 简易 Markdown 渲染
 *
 * 把 Markdown 文本拆分为 段落 / 代码块,对每段:
 *   - 围栏代码块 ```lang\n...\n``` → CodeBlock
 *   - 其他文本 → Text(RichText) 显示,markdown 子集映射成 HTML:
 *     **bold** / *italic* / `inline code` / [text](url) / ## 标题 / - 列表
 *
 * Props:
 *   markdown: string  原始 markdown 文本
 *   textColor: color  正文颜色
 *   linkColor: color  链接颜色
 */
Item {
    id: control

    property string markdown: ""
    property color textColor: Enums.textColor.primary
    property color linkColor: Enums.accentColor

    implicitHeight: contentColumn.implicitHeight
    implicitWidth: parent ? parent.width : 600

    // ==================== Block 解析 ====================
    // 把 markdown 按 ``` 分段:奇数段是代码块,偶数段是普通文本
    readonly property var _blocks: _parseBlocks(markdown)

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

        // flush
        if (inCode && codeBuf.length > 0) {
            blocks.push({ kind: "code", language: codeLang, content: codeBuf.join('\n') })
        }
        if (textBuf.length > 0) {
            blocks.push({ kind: "text", content: textBuf.join('\n') })
        }

        return blocks
    }

    // ==================== Render ====================
    ColumnLayout {
        id: contentColumn
        width: parent.width
        spacing: 8

        Repeater {
            model: control._blocks

            delegate: Loader {
                Layout.fillWidth: true
                required property var modelData
                sourceComponent: modelData.kind === "code" ? codeCmp : textCmp

                Component {
                    id: textCmp
                    Text {
                        // Qt 原生 CommonMark 解析: 有序/无序列表、加粗斜体、标题、
                        // 行内码、链接、段落换行全部正确 (替代旧手写正则,后者只支持子集)
                        text: modelData.content
                        color: control.textColor
                        linkColor: control.linkColor
                        textFormat: Text.MarkdownText
                        wrapMode: Text.WordWrap
                        font.family: Enums.fontFamily
                        font.pixelSize: 14
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
