// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// Import components 导入组件
import PrismQML
import PrismQML as Fluent

// Chat components page 聊天组件页面
Item {
    id: root

    ScrollArea {
        anchors.fill: parent

        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl

            // Page title 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { text: Fluent.Translator.tr("gallery_4b3510b8d86ea785", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
            }

            // Chat bubbles 聊天气泡
            ExampleCard {
                title: Fluent.Translator.tr("gallery_3b83a72ced370e25", Fluent.Translator._v)
                description: "role / content / timestamp / avatarText"
                Column {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ChatBubble {
                        width: 420
                        role: "assistant"
                        content: Fluent.Translator.tr("gallery_88a5b4642ba7c968", Fluent.Translator._v)
                        timestamp: "10:24"
                        avatarText: "P"
                    }
                    ChatBubble {
                        width: 420
                        role: "user"
                        content: Fluent.Translator.tr("gallery_00860ffb26e02643", Fluent.Translator._v)
                        timestamp: "10:25"
                    }
                    ChatBubble {
                        width: 420
                        role: "system"
                        content: Fluent.Translator.tr("gallery_1cec8d0ab7e9448e", Fluent.Translator._v)
                        timestamp: "10:26"
                    }
                }
            }

            // Code block 代码块
            ExampleCard {
                title: Fluent.Translator.tr("gallery_ddb4a628815d1385", Fluent.Translator._v)
                description: "code / language"
                ComponentCard {
                    label: "language: qml"
                    CodeBlock {
                        width: 420
                        language: "qml"
                        code: "import QtQuick\n\nRectangle {\n    width: 120\n    height: 48\n}"
                    }
                }
            }

            // Markdown view Markdown 渲染
            ExampleCard {
                title: Fluent.Translator.tr("gallery_c0b6fe57e6a0a585", Fluent.Translator._v)
                description: "markdown: headings / lists / fenced code"
                ComponentCard {
                    label: "markdown document"
                    MarkdownView {
                        width: 460
                        markdown: "# Heading\n\nParagraph with **bold** text.\n\n- first item\n- second item\n\n```js\nconsole.log('hello')\n```"
                    }
                }
            }
        }
    }
}
