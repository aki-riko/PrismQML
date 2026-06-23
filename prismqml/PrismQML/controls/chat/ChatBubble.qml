// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."
import "../../effects"
import "../icons"
import "../data/Avatar"
import "."

/**
 * ChatBubble — 单条消息气泡 (Copilot 卡片流)
 *
 * 用户消息靠右、强调色实底、白字、右下尖角;
 * 助手消息靠左、卡片色实底 + 边框 + level2 阴影 + 左侧头像、左上尖角;
 * 系统消息居中、淡底。
 * 内容用 MarkdownView 渲染。
 *
 * Props:
 *   role: string          "user" | "assistant" | "system"
 *   content: string       Markdown 文本
 *   timestamp: string     可选时间戳 (右下角小字)
 *   maxBubbleWidth: int   气泡最大宽度 (px),超出会折行
 *   avatarText: string    助手头像文字 (兜底,如 "DS")
 *   avatarSource: url      助手头像图片 (优先于文字)
 *   showAvatar: bool       助手消息是否显示左侧头像
 */
Item {
    id: control

    property string role: "assistant"
    property string content: ""
    property string reasoning: ""             // 思考链文本 (推理模型,仅助手消息)
    property string timestamp: ""
    property int maxBubbleWidth: 600
    property string avatarText: ""
    property url avatarSource: ""
    property bool showAvatar: true

    readonly property bool _isUser: role === "user"
    readonly property bool _isSystem: role === "system"
    readonly property bool _hasAvatar: !_isUser && !_isSystem && showAvatar
    readonly property bool _hasReasoning: !_isUser && !_isSystem && reasoning !== ""
    // 思考区展开状态: 流式思考中默认展开,正文开始(content 非空)后自动折叠
    property bool _reasoningExpanded: true
    property bool _userToggledReasoning: false   // 用户手动点过后不再自动折叠
    onContentChanged: {
        if (content !== "" && !_userToggledReasoning) _reasoningExpanded = false
    }
    readonly property int _avatarSize: 28
    readonly property int _avatarGap: Enums.spacing.m   // 8
    readonly property int _sideMargin: Enums.spacing.xl // 16
    readonly property int _pad: Enums.spacing.l         // 12

    // 可用宽度 (扣掉左右边距 + 助手头像占位)
    readonly property real _availWidth: {
        var w = control.width - _sideMargin * 2
        if (_hasAvatar) w -= (_avatarSize + _avatarGap)
        return Math.max(0, w)
    }

    // 用纯文本测量内容自然宽度 → 让短消息气泡包裹内容,不强行撑满 maxBubbleWidth
    TextMetrics {
        id: _metrics
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.body
        text: control.content.replace(/[#*`>\-]/g, "")  // 粗略剥离 markdown 记号
    }
    // 气泡内容区目标宽度
    readonly property real _bubbleWidth: {
        var natural = _metrics.advanceWidth + _pad * 2 + 4
        var cap = Math.min(control.maxBubbleWidth, _availWidth)
        return Math.max(48, Math.min(natural, cap))
    }

    // ==================== Auto Sizing ====================
    implicitHeight: bubble.y + bubble.height + Enums.spacing.xl  // 上下留白 (修复顶部被裁切)
    implicitWidth: parent ? parent.width : 800

    // ==================== 思考链折叠区 (仅助手, 轻量内联, 在气泡上方) ====================
    Item {
        id: reasoningBlock
        visible: control._hasReasoning
        anchors.top: parent.top
        anchors.topMargin: control._hasReasoning ? Enums.spacing.m : 0
        anchors.left: parent.left
        anchors.leftMargin: control._sideMargin
        anchors.right: parent.right
        anchors.rightMargin: control._sideMargin
        height: control._hasReasoning
                ? (reasoningHeader.height + (control._reasoningExpanded ? reasoningText.implicitHeight + Enums.spacing.xs : 0))
                : 0

        // 折叠头: chevron + "已深度思考" (一行, 可点击)
        Row {
            id: reasoningHeader
            anchors.top: parent.top
            anchors.left: parent.left
            height: Enums.iconSize.tiny + Enums.spacing.xs
            spacing: Enums.spacing.xs

            Icon {
                anchors.verticalCenter: parent.verticalCenter
                iconSize: Enums.iconSize.tiny
                icon: Enums.icon.chevron_down
                color: Enums.textColor.tertiary
                rotation: control._reasoningExpanded ? 0 : -90
                Behavior on rotation {
                    NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutQuad }
                }
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: "已深度思考"
                font.family: Enums.fontFamily
                font.pixelSize: Enums.typography.caption
                color: Enums.textColor.tertiary
            }
        }

        MouseArea {
            anchors.fill: reasoningHeader
            cursorShape: Qt.PointingHandCursor
            onClicked: {
                control._userToggledReasoning = true
                control._reasoningExpanded = !control._reasoningExpanded
            }
        }

        // 展开的思考文本 (灰色弱化, markdown 渲染, 无气泡背景)
        MarkdownView {
            id: reasoningText
            anchors.top: reasoningHeader.bottom
            anchors.topMargin: Enums.spacing.xs
            anchors.left: parent.left
            anchors.right: parent.right
            visible: control._reasoningExpanded
            markdown: control.reasoning
            textColor: Enums.textColor.tertiary
            linkColor: Enums.textColor.secondary
        }
    }

    // ==================== Assistant Avatar (左侧) ====================
    Avatar {
        id: avatar
        visible: control._hasAvatar
        size: control._avatarSize
        text: control.avatarText
        source: control.avatarSource !== "" ? String(control.avatarSource) : ""

        anchors.left: parent.left
        anchors.leftMargin: control._sideMargin
        anchors.top: reasoningBlock.bottom
        anchors.topMargin: Enums.spacing.m
    }

    // ==================== Shadow Layer (仅助手卡片) ====================
    // Fluent: 模糊阴影; neo: 硬阴影
    RectangularShadow {
        visible: !control._isUser && !control._isSystem && !Enums.isNeobrutalism
        anchors.fill: bubble
        radius: Enums.radius.large
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset: Qt.vector2d(0, Enums.shadow.level2.offset)
    }

    NeoShadow {
        target: bubble
        visible: !control._isUser && !control._isSystem && Enums.isNeobrutalism
        radius: Enums.radius.large
        z: bubble.z - 1
    }

    // ==================== Bubble ====================
    Rectangle {
        id: bubble
        // bubble 宽 = 内容自然宽 (上限 maxBubbleWidth 与可用宽)
        width: control._bubbleWidth
        height: content_.implicitHeight + control._pad * 2

        anchors.top: reasoningBlock.bottom
        anchors.topMargin: Enums.spacing.m

        // 靠左 / 靠右 / 居中(system)
        anchors.left: {
            if (control._isUser || control._isSystem) return undefined
            return control._hasAvatar ? avatar.right : parent.left
        }
        anchors.leftMargin: control._hasAvatar ? control._avatarGap : control._sideMargin
        anchors.right: control._isUser ? parent.right : undefined
        anchors.rightMargin: control._sideMargin
        anchors.horizontalCenter: control._isSystem ? parent.horizontalCenter : undefined

        // 非对称圆角: 用户右下尖, 助手左上尖, system 全圆
        radius: Enums.radius.large
        topLeftRadius: control._isUser ? Enums.radius.large : Enums.radius.small
        topRightRadius: Enums.radius.large
        bottomLeftRadius: Enums.radius.large
        bottomRightRadius: control._isUser ? Enums.radius.small : Enums.radius.large

        color: {
            if (control._isSystem) return Enums.hoverColor
            if (control._isUser) return Enums.accentColor
            return Enums.cardColor
        }
        // neo: 所有气泡黑粗边(含用户气泡); Fluent: 仅助手细边
        border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : (control._isUser ? 0 : Enums.border.thin)
        border.color: Enums.isNeobrutalism ? Enums.neo.borderColor : (control._isUser ? "transparent" : Enums.borderColor)

        // ==================== Content ====================
        MarkdownView {
            id: content_
            anchors.fill: parent
            anchors.margins: control._pad  // 12

            markdown: control.content
            textColor: control._isUser ? Enums.accentForeground : Enums.textColor.primary
            linkColor: control._isUser ? Enums.accentForeground : Enums.accentColor
        }

        // ==================== Timestamp (可选) ====================
        Text {
            visible: control.timestamp !== ""
            text: control.timestamp
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: Enums.spacing.s
            font.pixelSize: Enums.typography.tiny + 1
            font.family: Enums.fontFamily
            color: control._isUser ? Qt.rgba(1, 1, 1, 0.6) : Enums.textColor.tertiary
        }
    }
}
