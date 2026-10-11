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
                Text { text: "Chat"; font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
            }

            // Chat bubbles 聊天气泡
            ExampleCard {
                title: "ChatBubble"
                description: "role / content / timestamp / avatarText"
                Column {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l
                    ChatBubble {
                        width: 420
                        role: "assistant"
                        content: "Assistant reply rendered by ChatBubble."
                        timestamp: "10:24"
                        avatarText: "P"
                    }
                    ChatBubble {
                        width: 420
                        role: "user"
                        content: "User message uses the accent surface."
                        timestamp: "10:25"
                    }
                    ChatBubble {
                        width: 420
                        role: "system"
                        content: "System notice row."
                        timestamp: "10:26"
                    }
                }
            }

            // Code block 代码块
            ExampleCard {
                title: "CodeBlock"
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
                title: "MarkdownView"
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
