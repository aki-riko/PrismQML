// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import PrismQML as Fluent

// AIAssistantPage - AI assistant and chat bubble gallery page AI 助手与聊天气泡展示页
//
// 三块内容：
//   1. 聊天气泡：ChatMessageList + ChatBubble，覆盖 markdown、行内代码、围栏代码块与推理折叠；
//   2. 气泡壳：ChatBubbleSurface 的 role / tail / elevationOnUser 取舍矩阵，并可直接切皮肤看它跟随；
//   3. SSE 流式输出：真实 `text/event-stream` 传输（固定话术的本地演示后端）驱动增量渲染。
//
// 🔴 演示话术一律来自 `aiAssistantDemo`（Python 侧），不写进本文件：Gallery 的 i18n 门禁会把
//    QML 里的中文与面向用户的英文串登记成待翻译项，演示内容不该逼着 20 份语言目录各翻一遍。
Item {
    id: root

    // 演示后端由 Gallery 宿主注入；单独加载本页（测试）时允许缺席。
    readonly property var demo: typeof aiAssistantDemo !== "undefined" ? aiAssistantDemo : null
    readonly property var stream: root.demo ? root.demo.stream : null
    readonly property bool demoAvailable: root.demo ? root.demo.available : false
    readonly property bool streaming: root.stream ? root.stream.streaming : false
    readonly property int streamFrameCount: root.stream ? root.stream.frameCount : 0

    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
    }

    // 静态会话：逐条追加，带推理的那条紧跟其后补推理文本（appendReasoningToLast 作用于最后一条）。
    function loadPreviewMessages() {
        if (!root.demo || !previewList) return
        previewList.clear()
        var messages = root.demo.previewMessages
        for (var i = 0; i < messages.length; i++) {
            var message = messages[i]
            previewList.appendMessage(message.role, message.content, message.timestamp)
            if (message.reasoning) previewList.appendReasoningToLast(message.reasoning)
        }
    }

    function startStream() {
        if (!root.demoAvailable || root.streaming || !streamList) return
        streamList.clear()
        streamList.appendMessage("assistant", "", "")
        root.stream.start()
    }

    function streamStatusText() {
        if (!root.demoAvailable) return root.demo ? root.demo.errorText : "demo backend unavailable"
        if (root.streaming) return "streaming · frames: " + root.streamFrameCount
        return root.streamFrameCount > 0 ? "finished · frames: " + root.streamFrameCount : "idle"
    }

    function skinLabel(skin) {
        switch (skin) {
        case "fluent":
            return Fluent.Translator.tr("skin_fluent_design", Fluent.Translator._v)
        case "neobrutalism":
            return Fluent.Translator.tr("skin_neobrutalism", Fluent.Translator._v)
        case "vintage_ticket":
            return Fluent.Translator.tr("skin_vintage_ticket", Fluent.Translator._v)
        case "neumorphism":
            return Fluent.Translator.tr("skin_neumorphism", Fluent.Translator._v)
        default:
            return skin
        }
    }

    // 流式增量：推理走 appendReasoningToLast，正文走 appendToLast；
    // 两条都只追加文本，列表自己负责滚动跟随。
    Connections {
        target: root.stream

        function onReasoningChunk(text) {
            if (streamList) streamList.appendReasoningToLast(text)
        }

        function onDeltaChunk(text) {
            if (streamList) streamList.appendToLast(text)
        }

        function onFailed(message) {
            console.log("GALLERY_ASSISTANT_STREAM_FAILED", message)
        }
    }

    Component.onCompleted: root.loadPreviewMessages()

    Fluent.ScrollArea {
        anchors.fill: parent

        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl

            // Page title 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs

                Fluent.Label {
                    type: Fluent.Enums.label.type_title
                    text: Fluent.Translator.tr("gallery_1b0049fcfd4163fe", Fluent.Translator._v)
                }
            }

            // Chat bubbles 聊天气泡
            Fluent.ExampleCard {
                title: Fluent.Translator.tr("gallery_3b83a72ced370e25", Fluent.Translator._v)
                description: "ChatMessageList / ChatBubble / MarkdownView / CodeBlock"

                Fluent.ChatMessageList {
                    id: previewList
                    objectName: "galleryPreviewMessageList"
                    width: parent ? parent.width : 0
                    height: 420
                    assistantAvatarText: "P"
                }
            }

            // Bubble shell 气泡壳
            Fluent.ExampleCard {
                title: Fluent.Translator.tr("gallery_92ee8f68a7ea40ae", Fluent.Translator._v)
                description: "ChatBubbleSurface / role / tail / elevationOnUser"

                Column {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l

                    // 换皮肤：外壳的配色、描边与阴影层级全部来自令牌，切一下就能看见它跟随。
                    Row {
                        spacing: Fluent.Enums.spacing.s

                        Repeater {
                            model: (typeof ConfigManager !== "undefined" && ConfigManager)
                                   ? ConfigManager.skinOptions : []

                            Fluent.Button {
                                text: root.skinLabel(modelData)
                                style: (ConfigManager && ConfigManager.skin === modelData)
                                       ? Fluent.Enums.button.style_primary
                                       : Fluent.Enums.button.style_default
                                onClicked: ConfigManager.setSkin(modelData)
                            }
                        }
                    }

                    Flow {
                        width: parent ? parent.width : 0
                        spacing: Fluent.Enums.spacing.l

                        Repeater {
                            model: root.demo ? root.demo.surfaceShowcase : []

                            Column {
                                spacing: Fluent.Enums.spacing.xs

                                Fluent.ChatBubbleSurface {
                                    width: 240
                                    height: 44
                                    role: modelData.role
                                    tail: modelData.tail
                                    elevationOnUser: modelData.elevationOnUser
                                    chromeless: modelData.label === "chromeless: true"

                                    Fluent.Label {
                                        anchors.centerIn: parent
                                        type: Fluent.Enums.label.type_caption
                                        text: modelData.label
                                        color: modelData.role === "user"
                                               ? Fluent.Enums.accentForeground
                                               : Fluent.Enums.textColor.primary
                                    }
                                }

                                Fluent.Label {
                                    type: Fluent.Enums.label.type_caption
                                    text: modelData.label
                                    color: Fluent.Enums.textColor.secondary
                                }
                            }
                        }
                    }
                }
            }

            // SSE streaming SSE 流式输出
            Fluent.ExampleCard {
                title: Fluent.Translator.tr("gallery_56062030e374faf2", Fluent.Translator._v)
                description: "text/event-stream · reasoning / delta / done"

                Column {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.m

                    Row {
                        spacing: Fluent.Enums.spacing.s

                        Fluent.Button {
                            objectName: "galleryAssistantStartButton"
                            text: Fluent.Translator.tr("gallery_d2bb025a2e51c410", Fluent.Translator._v)
                            enabled: root.demoAvailable && !root.streaming
                            onClicked: root.startStream()
                        }

                        Fluent.Button {
                            objectName: "galleryAssistantCancelButton"
                            text: Fluent.Translator.tr("gallery_f9d19345a067cbe1", Fluent.Translator._v)
                            enabled: root.streaming
                            onClicked: {
                                if (root.stream) root.stream.cancel()
                            }
                        }

                        Fluent.Label {
                            objectName: "galleryAssistantStreamStatus"
                            anchors.verticalCenter: parent.verticalCenter
                            type: Fluent.Enums.label.type_caption
                            text: root.streamStatusText()
                            color: Fluent.Enums.textColor.secondary
                        }
                    }

                    Fluent.ChatMessageList {
                        id: streamList
                        objectName: "galleryStreamMessageList"
                        width: parent ? parent.width : 0
                        height: 320
                        assistantAvatarText: "P"
                    }
                }
            }
        }
    }
}
