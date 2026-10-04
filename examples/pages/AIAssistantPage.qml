// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import PrismQML as Fluent

// AIAssistantPage - AI assistant chat surface AI 助手对话页
//
// 一整页就是一个对话框：顶部身份条、中间消息区、底部输入条。用户发出问题后，助手气泡按
// **真实 SSE** 增量吐出内容（固定话术的本地演示后端，见 examples/ai_demo）。
//
// 这里刻意不做成"组件卡片陈列"：Gallery 的其它页面已经逐个展示过组件，这一页要看的是它们
// 组合起来像一个真东西时是什么样——消息列表撑满、输入条常驻、空态给建议、流式中可中断。
//
// 🔴 演示话术与建议问题一律来自 `aiAssistantDemo`（Python 侧），不写进本文件：Gallery 的
//    i18n 门禁会把 QML 里的中文与面向用户的英文串登记成待翻译项，演示内容不该逼着 20 份
//    语言目录各翻一遍。
Item {
    id: root

    // 演示后端由 Gallery 宿主注入；单独加载本页（测试）时允许缺席。
    readonly property var demo: typeof aiAssistantDemo !== "undefined" ? aiAssistantDemo : null
    readonly property var stream: root.demo ? root.demo.stream : null
    readonly property bool streaming: root.stream ? root.stream.streaming : false
    readonly property bool backendReady: root.demo ? root.demo.available : false
    readonly property bool canSend: root.backendReady && !root.streaming
    readonly property bool canStop: root.streaming
    property bool hasConversation: false

    function clockText() {
        var now = new Date()
        var hours = String(now.getHours())
        var minutes = String(now.getMinutes())
        if (hours.length < 2) hours = "0" + hours
        if (minutes.length < 2) minutes = "0" + minutes
        return hours + ":" + minutes
    }

    // 发送：先把用户这句落进列表，再补一条空的助手消息，然后开流（增量都追加到它身上）。
    function sendPrompt(rawText) {
        var prompt = String(rawText === undefined || rawText === null ? "" : rawText).trim()
        if (prompt.length === 0 || !root.canSend) return
        composer.text = ""
        chatList.appendMessage("user", prompt, root.clockText())
        chatList.appendMessage("assistant", "", root.clockText())
        root.hasConversation = true
        root.stream.start()
    }

    function stopStream() {
        if (root.stream) root.stream.cancel()
    }

    function clearConversation() {
        if (root.streaming) root.stopStream()
        chatList.clear()
        root.hasConversation = false
    }

    // 状态文案保持技术口径（英文），不占用目录条目：idle / streaming · frames: N / finished · frames: N
    function statusText() {
        if (!root.backendReady) return root.demo ? root.demo.errorText : "demo backend unavailable"
        var prefix = Fluent.Translator.tr("gallery_56062030e374faf2", Fluent.Translator._v)
        if (root.streaming) return prefix + " · streaming · frames: " + (root.stream ? root.stream.frameCount : 0)
        var frames = root.stream ? root.stream.frameCount : 0
        return frames > 0 ? prefix + " · finished · frames: " + frames : prefix + " · idle"
    }

    // 流式增量：推理走 appendReasoningToLast，正文走 appendToLast；失败就把原因写进气泡，
    // 让用户看见"这一条没跑完"，而不是静默停在半截。
    Connections {
        target: root.stream

        function onReasoningChunk(text) {
            chatList.appendReasoningToLast(text)
        }

        function onDeltaChunk(text) {
            chatList.appendToLast(text)
        }

        function onFailed(message) {
            chatList.appendToLast("\n\n" + message)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ==================== 身份条 ====================
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: Fluent.Enums.spacing.l
            Layout.rightMargin: Fluent.Enums.spacing.l
            Layout.topMargin: Fluent.Enums.spacing.m
            Layout.bottomMargin: Fluent.Enums.spacing.m
            spacing: Fluent.Enums.spacing.m

            Rectangle {
                Layout.alignment: Qt.AlignVCenter
                implicitWidth: Fluent.Enums.controlSize.inputHeight
                implicitHeight: Fluent.Enums.controlSize.inputHeight
                radius: width / 2
                color: Fluent.Enums.accentColor

                Fluent.Icon {
                    anchors.centerIn: parent
                    icon: Fluent.Enums.icon.bot_sparkle
                    iconSize: Fluent.Enums.iconSize.small
                    color: Fluent.Enums.accentForeground
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0

                Fluent.Label {
                    objectName: "galleryAssistantTitle"
                    type: Fluent.Enums.label.type_subtitle
                    text: Fluent.Translator.tr("gallery_1b0049fcfd4163fe", Fluent.Translator._v)
                }

                Fluent.Label {
                    objectName: "galleryAssistantStatus"
                    type: Fluent.Enums.label.type_caption
                    color: Fluent.Enums.textColor.secondary
                    text: root.statusText()
                }
            }

            Fluent.Button {
                objectName: "galleryAssistantClearButton"
                Layout.alignment: Qt.AlignVCenter
                icon: Fluent.Enums.icon.broom_sparkle
                enabled: root.hasConversation
                onClicked: root.clearConversation()
            }
        }

        // ==================== 消息区 ====================
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Fluent.ChatMessageList {
                id: chatList
                objectName: "galleryAssistantChatList"
                anchors.fill: parent
                assistantAvatarText: "P"
            }

            // 空态：一句引导 + 可以点的建议问题（文案来自 Python）。发过消息就不再出现。
            ColumnLayout {
                objectName: "galleryAssistantEmptyState"
                anchors.centerIn: parent
                width: Math.min(parent.width - Fluent.Enums.spacing.xxl * 2,
                                Fluent.Enums.controlSize.chatContentMaxWidth)
                spacing: Fluent.Enums.spacing.m
                visible: !root.hasConversation

                Fluent.Icon {
                    Layout.alignment: Qt.AlignHCenter
                    icon: Fluent.Enums.icon.bot_sparkle
                    iconSize: Fluent.Enums.iconSize.xxxl
                    color: Fluent.Enums.textColor.tertiary
                }

                Repeater {
                    model: root.demo ? root.demo.suggestions : []

                    Fluent.Button {
                        objectName: "galleryAssistantSuggestion" + index
                        Layout.fillWidth: true
                        style: Fluent.Enums.button.style_default
                        text: modelData
                        enabled: root.canSend
                        onClicked: root.sendPrompt(modelData)
                    }
                }
            }
        }

        // ==================== 输入条 ====================
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: Fluent.Enums.spacing.l
            Layout.rightMargin: Fluent.Enums.spacing.l
            Layout.topMargin: Fluent.Enums.spacing.m
            Layout.bottomMargin: Fluent.Enums.spacing.l
            spacing: Fluent.Enums.spacing.s

            Fluent.LineEdit {
                id: composer
                objectName: "galleryAssistantComposer"
                Layout.fillWidth: true
                placeholderText: Fluent.Translator.tr("placeholder_input", Fluent.Translator._v)
                clearButtonEnabled: false
                enabled: root.canSend
                onAccepted: root.sendPrompt(text)
            }

            Fluent.Button {
                objectName: "galleryAssistantSendButton"
                Layout.alignment: Qt.AlignVCenter
                style: Fluent.Enums.button.style_primary
                icon: root.canStop ? Fluent.Enums.icon.stop : Fluent.Enums.icon.send
                enabled: root.canStop || (root.canSend && composer.text.trim().length > 0)
                onClicked: root.canStop ? root.stopStream() : root.sendPrompt(composer.text)
            }
        }
    }
}
