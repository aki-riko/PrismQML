// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../.."
import "../../effects"
import "../icons"
import "../data/Avatar"
import "."

/**
 * ChatBubble - Single-message bubble in a Copilot-style card flow Copilot 卡片流中的单条消息气泡
 *
 * User messages align right with an accent background and lower-right tail 用户消息右对齐并使用强调色背景和右下尖角
 * Assistant messages align left with a bordered, shadowed card and avatar 助手消息左对齐并显示带边框阴影的卡片和头像
 * System messages use a centered subtle background 系统消息居中并使用弱化背景
 * MarkdownView renders message content 消息内容由 MarkdownView 渲染
 *
 * Props 公开属性:
 *   role: string          Message role 消息角色："user" | "assistant" | "system"
 *   content: string       Markdown content Markdown 内容
 *   timestamp: string     Optional lower-right timestamp 可选右下角时间戳
 *   maxBubbleWidth: int   Maximum bubble width before wrapping 气泡折行前的最大宽度
 *   avatarText: string    Assistant avatar fallback text 助手头像兜底文字
 *   avatarSource: url     Preferred assistant avatar image 助手头像图片优先来源
 *   showAvatar: bool      Whether to show the assistant avatar 是否显示助手头像
 */
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string role: "assistant"
    property string content: ""
    // Reasoning text for assistant messages 助手消息的推理文本
    property string reasoning: ""
    property string timestamp: ""
    property int maxBubbleWidth: Enums.controlSize.chatContentMaxWidth
    property string avatarText: ""
    property url avatarSource: ""
    property bool showAvatar: true

    // ==================== Internal Props 内部属性 ====================
    // Keep reasoning expanded while streaming, then collapse when content starts
    // 流式推理期间保持展开，正文开始后自动折叠
    property bool _reasoningExpanded: true
    // Preserve the user's explicit toggle choice 保留用户的手动展开选择
    property bool _userToggledReasoning: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isUser: role === "user"
    readonly property bool _isSystem: role === "system"
    readonly property bool _hasAvatar: !_isUser && !_isSystem && showAvatar
    readonly property bool _hasReasoning: !_isUser && !_isSystem && reasoning !== ""
    readonly property int _bubbleRadius: Enums.surfaceRadius(Enums.radius.large)
    readonly property int _bubbleTailRadius: Enums.surfaceRadius(Enums.radius.small)
    readonly property color _assistantBubbleBackground: Enums.cardColor
    readonly property color _userBubbleBackground: Enums.accentColor
    readonly property color _systemBubbleBackground: Enums.hoverColor
    readonly property color _bubbleBackground: _isSystem ? _systemBubbleBackground : (_isUser ? _userBubbleBackground : _assistantBubbleBackground)
    readonly property real _bubbleBorderWidth: Enums.hasOutlinedSurfaces
        ? Enums.surfaceBorderWidth(Enums.border.thin) : (_isUser ? 0 : Enums.border.thin)
    readonly property color _bubbleBorderColor: Enums.hasOutlinedSurfaces
        ? Enums.borderColor : (_isUser ? Enums.transparent : Enums.borderColor)
    readonly property color _contentTextColor: _isUser ? Enums.accentForeground : Enums.textColor.primary
    readonly property color _contentLinkColor: _isUser ? Enums.accentForeground : Enums.accentColor
    readonly property color _reasoningTextColor: Enums.textColor.tertiary
    readonly property color _reasoningLinkColor: Enums.textColor.secondary
    readonly property color _timestampColor: _isUser
        ? Enums.textColor.onAccentTimestamp
        : Enums.textColor.tertiary
    readonly property color _assistantShadowColor: Enums.shadow.level2.color
    readonly property real _assistantShadowBlur: Enums.shadow.level2.blur
    readonly property real _assistantShadowOffset: Enums.shadow.level2.offset
    readonly property int _avatarSize: 28
    readonly property int _avatarGap: Enums.spacing.m
    readonly property int _sideMargin: Enums.spacing.xl
    readonly property int _pad: Enums.spacing.l
    // 时间戳**绝不能压在正文上**。此前它直接锚在气泡内右下角，正文又铺满整个气泡，于是每一
    // 条带时间戳的消息最后一行都被盖住（实测：单字消息里 "2" 与 "04:26" 直接叠在一起）。
    // 现在的规则是「放得下就内联在末行右侧，放不下才在气泡内另起一行」：
    readonly property bool _hasTimestamp: control.timestamp !== ""
    readonly property real _timestampGap: Enums.spacing.s
    // 🔴 判据必须**只看字体度量**，绝不能读渲染后的正文高度：正文高度取决于它拿到的宽度，
    //    而宽度又取决于这里的判据——一读就成环（实测 MarkdownView 刷 "polish() loop"、
    //    正文高度飙到 882px）。所以用 TextMetrics 按最大可用宽度量一次换行结果。
    readonly property real _capWidth: Math.min(control.maxBubbleWidth, _availWidth)
    readonly property real _contentMaxWidth: Math.max(0, _capWidth - _pad * 2)
    // 会不会换行只看度量：有显式换行，或单行自然宽度超过正文最大宽度。
    readonly property bool _contentSingleLine: control.content.indexOf("\n") < 0
        && _metrics.advanceWidth <= _contentMaxWidth + 0.5
    readonly property bool _timestampInline: _hasTimestamp && _contentSingleLine
        && (_metrics.advanceWidth + _timestampGap + _timestampMetrics.advanceWidth
            + _pad * 2 + 4) <= _capWidth
    // 内联时正文右侧必须**留出时间戳那一条**：只把气泡加宽是不够的——正文条目仍占满整宽，
    // 结构上依旧重叠（实测条目矩形相交）。留出条带后两种模式都互斥，且不依赖度量完全准确。
    readonly property real _contentRightInset: _timestampInline
        ? _pad + _timestampMetrics.advanceWidth + _timestampGap : _pad
    // 另起一行时给时间戳预留的带状高度（含与正文的间距）。
    readonly property real _footerHeight: _hasTimestamp && !_timestampInline
        ? _timestampMetrics.height + _timestampGap * 0.5 : 0
    // Available width after side margins and avatar space 扣除左右边距和头像占位后的可用宽度
    readonly property real _availWidth: {
        var w = control.width - _sideMargin * 2
        if (_hasAvatar) w -= (_avatarSize + _avatarGap)
        return Math.max(0, w)
    }
    // 最小宽度还要容得下时间戳：否则短消息的气泡会被时间戳挤变形（实测单字消息只有 48px）。
    readonly property real _minBubbleWidth: Math.max(48, _hasTimestamp
        ? _pad * 2 + _timestampMetrics.advanceWidth : 0)
    // Target bubble width based on natural text width 气泡基于文本自然宽度的目标宽度
    readonly property real _bubbleWidth: {
        var natural = _metrics.advanceWidth + _pad * 2 + 4
        if (_timestampInline) natural += _timestampGap + _timestampMetrics.advanceWidth
        return Math.max(_minBubbleWidth, Math.min(natural, _capWidth))
    }

    // ==================== Size 尺寸 ====================
    implicitHeight: bubble.y + bubble.height + Enums.spacing.xl
    implicitWidth: parent ? parent.width : 800

    onContentChanged: {
        if (content !== "" && !_userToggledReasoning) _reasoningExpanded = false
    }

    // Measure plain-text width so short messages wrap their content instead of filling the cap
    // 使用纯文本宽度让短消息包裹内容，而不是强行撑满上限
    TextMetrics {
        id: _metrics
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.body
        // Strip common Markdown markers approximately 粗略剥离常见 Markdown 记号
        text: control.content.replace(/[#*`>\-]/g, "")
    }

    // 时间戳宽度/高度：内联条带与另起一行的高度都靠它。
    TextMetrics {
        id: _timestampMetrics
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.tiny + 1
        text: control.timestamp
    }

    // ==================== Content 内容 ====================
    // Collapsible reasoning block for assistant messages 助手消息的可折叠推理区
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

        // Clickable one-line header with a chevron 带箭头的可点击单行标题
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
                text: { Translator._v; return Translator.tr("deep_thought") }
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

        // Expanded muted Markdown reasoning without a bubble background
        // 展开后的弱化 Markdown 推理文本，不显示气泡背景
        MarkdownView {
            id: reasoningText
            anchors.top: reasoningHeader.bottom
            anchors.topMargin: Enums.spacing.xs
            anchors.left: parent.left
            anchors.right: parent.right
            visible: control._reasoningExpanded
            markdown: control.reasoning
            textColor: control._reasoningTextColor
            linkColor: control._reasoningLinkColor
        }
    }

    // Left-side assistant avatar 左侧助手头像
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

    // Message bubble 消息气泡
    // The shell (color / radius / tail / border / elevation across all four skins) comes from
    // ChatBubbleSurface, shared with downstream chat surfaces. 外壳（配色 / 圆角 / 尖角 /
    // 描边 / 四种皮肤下的阴影）统一由 ChatBubbleSurface 提供，与下游聊天界面共用。
    ChatBubbleSurface {
        id: bubble
        role: control.role
        // Copilot card flow keeps blurred / hard elevation on assistant messages only.
        // 卡片流只给助手消息留模糊与硬阴影（新拟态按皮肤语义两侧都留）。
        elevationOnUser: false
        neumorphicAccent: control._isUser

        // Natural content width capped by maxBubbleWidth and available width
        // 内容自然宽度受 maxBubbleWidth 和可用宽度限制
        width: control._bubbleWidth
        // 另起一行放时间戳时，底部留出带状高度；内联时不额外增高。
        height: content_.implicitHeight + control._pad * 2 + control._footerHeight

        anchors.top: reasoningBlock.bottom
        anchors.topMargin: Enums.spacing.m

        // Align assistant left, user right, and system center 助手左对齐、用户右对齐、系统居中
        anchors.left: {
            if (control._isUser || control._isSystem) return undefined
            return control._hasAvatar ? avatar.right : parent.left
        }
        anchors.leftMargin: control._hasAvatar ? control._avatarGap : control._sideMargin
        anchors.right: control._isUser ? parent.right : undefined
        anchors.rightMargin: control._sideMargin
        anchors.horizontalCenter: control._isSystem ? parent.horizontalCenter : undefined

        // Markdown content Markdown 内容
        // 底部反缩进 `_footerHeight`：时间戳另起一行时正文让出那一条带，两者不再重叠。
        MarkdownView {
            id: content_
            objectName: "chatBubbleContent"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.leftMargin: control._pad
            anchors.rightMargin: control._contentRightInset
            anchors.topMargin: control._pad
            anchors.bottomMargin: control._pad + control._footerHeight

            markdown: control.content
            textColor: control._contentTextColor
            linkColor: control._contentLinkColor
        }

        // Optional timestamp 可选时间戳
        // 内联：与单行正文同一行右侧；另起一行：落进正文让出的底部带状区。两种都不会压住正文。
        Text {
            id: timestamp_
            objectName: "chatBubbleTimestamp"
            visible: control._hasTimestamp
            text: control.timestamp
            font.pixelSize: Enums.typography.tiny + 1
            font.family: Enums.fontFamily
            color: control._timestampColor
            anchors.right: parent.right
            anchors.rightMargin: control._pad
            anchors.bottom: parent.bottom
            anchors.bottomMargin: control._timestampInline
                ? control._pad : control._pad * 0.5
        }
    }
}
