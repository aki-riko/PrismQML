// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../../.."
import "."
import "../containers/ScrollBar"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

/**
 * ChatMessageList — 消息列表 (变高 ListView + SmoothScrollHelper + ScrollBar)
 *
 * 接 ListModel,每项含 { role, content, timestamp }。
 * 用 FluentQML SmoothScrollHelper 接管滚轮 → 平滑滚动 + 边界回弹;
 * 自动滚到底部、消息更新时保持位置。
 * 气泡变高,故不套 ScrollArea 的虚拟化定高列表 (type_list 要求 itemHeight 等高)。
 *
 * Public methods:
 *   appendMessage(role, content, timestamp)
 *   updateLastContent(text)         流式更新最后一条 content
 *   appendToLast(chunk)             给最后一条 content 追加 chunk
 *   setLastContent(text)            ↔ updateLastContent (别名)
 *   clear()                         清空
 *   scrollToEnd()                   主动滚到底
 *
 * Public props:
 *   maxBubbleWidth: int             转发给 ChatBubble
 *   assistantAvatarText: string     助手气泡头像文字 (兜底)
 *   assistantAvatarSource: url      助手气泡头像图片
 *   showAssistantAvatar: bool       是否显示助手头像
 */
Item {
    id: control

    property int maxBubbleWidth: 600
    property string assistantAvatarText: ""
    property url assistantAvatarSource: ""
    property bool showAssistantAvatar: true
    readonly property int messageCount: chatModel.count

    // 用户是否在底部 (容差 24px)
    readonly property bool _isAtBottom: listView.contentY + listView.height >= listView.contentHeight - 24

    // ==================== Public API ====================
    // 滚到底: positionViewAtEnd 同步改 contentY,再 callLater 把 SmoothScrollHelper
    // 内部 _smoothY/_targetY 同步到新位置,否则下次滚轮从旧位置跳变 → 滚动条手柄错位。
    function _scrollToBottom() {
        listView.positionViewAtEnd()
        Qt.callLater(function() {
            listView.positionViewAtEnd()
            scrollHelper.syncPosition()
        })
    }

    function appendMessage(role, content, timestamp) {
        chatModel.append({
            role: role || "assistant",
            content: content || "",
            reasoning: "",
            timestamp: timestamp || ""
        })
        _scrollToBottom()
    }

    // 给最后一条追加思考链 chunk (推理模型流式 reasoning_content)
    function appendReasoningToLast(chunk) {
        if (chatModel.count === 0) return
        var idx = chatModel.count - 1
        var prev = chatModel.get(idx).reasoning || ""
        chatModel.setProperty(idx, "reasoning", prev + chunk)
        if (control._isAtBottom) _scrollToBottom()
    }

    function updateLastContent(text) {
        if (chatModel.count === 0) return
        chatModel.setProperty(chatModel.count - 1, "content", text)
    }

    function setLastContent(text) {
        updateLastContent(text)
    }

    function appendToLast(chunk) {
        if (chatModel.count === 0) return
        var idx = chatModel.count - 1
        var prev = chatModel.get(idx).content || ""
        chatModel.setProperty(idx, "content", prev + chunk)
    }

    function clear() {
        chatModel.clear()
    }

    function scrollToEnd() {
        _scrollToBottom()
    }

    function getLastRole() {
        if (chatModel.count === 0) return ""
        return chatModel.get(chatModel.count - 1).role
    }

    ListView {
        id: listView
        anchors.fill: parent
        model: ListModel { id: chatModel }
        spacing: 4
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        // 关键: 滚动驱动权交给 SmoothScrollHelper 独占 (handleWheel)。
        // ListView 自身 interactive 会形成第二个滚动源 → 与 helper 的 _smoothY 各记一套
        // contentY,互相拽回 = "滚动界面回弹"。FluentQML ScrollAreaList/Default 同样 false。
        interactive: false
        // 气泡变高,ListView 对回收掉的 delegate 用平均高度估算 contentHeight,
        // 短用户气泡+长助手气泡交替时高估可达十几% → 能滚过真实底部露出大片空白。
        // 聊天消息数有限,用大 cacheBuffer 让 delegate 常驻 → contentHeight 精确。
        cacheBuffer: 1000000

        delegate: ChatBubble {
            width: listView.width
            role: model.role
            content: model.content
            reasoning: model.reasoning || ""
            timestamp: model.timestamp || ""
            maxBubbleWidth: control.maxBubbleWidth
            avatarText: control.assistantAvatarText
            avatarSource: control.assistantAvatarSource
            showAvatar: control.showAssistantAvatar
        }

        // 当列表内容变化时,如果用户已经在底部,则保持在底部 (流式追加跟随)
        onContentHeightChanged: {
            if (control._isAtBottom) control._scrollToBottom()
        }
    }

    // FluentQML 平滑滚动: 接管滚轮 → 缓动 + 边界回弹 (不主动驱动,仅响应滚轮)
    SmoothScrollHelper {
        id: scrollHelper
        target: listView
        orientation: Qt.Vertical
        handleWheel: true
    }

    ScrollBar {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.rightMargin: Enums.spacing.xxs
        target: listView
        scrollHelper: scrollHelper
        orientation: Qt.Vertical
        barWidth: Enums.spacing.s
        z: Enums.zIndex.controlsAbove
    }
}
