// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../.."
import "."
import "../containers/ScrollBar"
import QtQuick  // Place after library imports so native types keep no prefix 置于库 import 后，确保原生类型无需前缀

/**
 * ChatMessageList - Virtualized variable-height message list 变高消息虚拟列表
 *
 * Accepts messages containing { role, content, reasoning, timestamp } 接收消息字段。
 * Lightweight height slots stay resident while complex ChatBubble delegates only load
 * near the viewport, avoiding ListView's inaccurate variable-height estimation and
 * full-session delegate retention. 轻量高度占位常驻，复杂气泡仅在视口附近加载，
 * 同时规避 ListView 变高估算误差和整段会话常驻内存。
 *
 * Public methods 公开方法:
 *   appendMessage(role, content, timestamp)
 *   appendReasoningToLast(chunk)
 *   updateLastContent(text)
 *   appendToLast(chunk)
 *   setLastContent(text)
 *   clear()
 *   scrollToEnd()
 *   getLastRole()
 *
 * Public props 公开属性:
 *   maxBubbleWidth: int
 *   assistantAvatarText: string
 *   assistantAvatarSource: url
 *   showAssistantAvatar: bool
 */
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int maxBubbleWidth: Enums.controlSize.chatContentMaxWidth
    property string assistantAvatarText: ""
    property url assistantAvatarSource: ""
    property bool showAssistantAvatar: true

    // ==================== Internal Props 内部属性 ====================
    property bool _followBottom: true
    property bool _adjustingScroll: false
    property bool _scrollPending: false
    property bool _layoutPending: false
    property real _pendingAnchorDelta: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property int messageCount: chatModel.count
    readonly property real _loadMargin: Math.max(0, messageViewport.height)
    readonly property real _minimumMessageHeight:
        Enums.spacing.l * 2 + Enums.spacing.m + Enums.spacing.xl
    readonly property real _bottomTolerance: Enums.spacing.l * 2
    readonly property real _heightChangeTolerance: Enums.border.thin / 2
    readonly property bool _isAtBottom:
        messageViewport.contentY + messageViewport.height
        >= messageViewport.contentHeight - _bottomTolerance

    // ==================== Internal Methods 内部方法 ====================
    function _setContentY(contentY, keepFollowing) {
        var maximumY = Math.max(0, messageViewport.contentHeight - messageViewport.height)
        _adjustingScroll = true
        messageViewport.contentY = Math.max(0, Math.min(maximumY, contentY))
        scrollHelper.syncPosition()
        _adjustingScroll = false
        _followBottom = keepFollowing
    }

    function _scrollToBottom() {
        _setContentY(messageViewport.contentHeight - messageViewport.height, true)
    }

    function _scheduleScrollToBottom() {
        if (_scrollPending) return
        _scrollPending = true
        Qt.callLater(function() {
            _scrollPending = false
            if (_followBottom) _scrollToBottom()
        })
    }

    function _scheduleSlotLayout() {
        if (_layoutPending) return
        _layoutPending = true
        Qt.callLater(function() {
            _layoutPending = false
            var nextY = 0
            for (var i = 0; i < messageRepeater.count; i++) {
                var slot = messageRepeater.itemAt(i)
                if (!slot) continue
                slot.y = nextY
                nextY += slot.height
                if (i + 1 < messageRepeater.count) nextY += Enums.spacing.xs
                if (!slot._layoutReady) slot._layoutReady = true
            }
            messageColumn.height = nextY
            if (_followBottom) {
                _pendingAnchorDelta = 0
                _scheduleScrollToBottom()
            } else if (Math.abs(_pendingAnchorDelta) >= _heightChangeTolerance) {
                var anchorDelta = _pendingAnchorDelta
                _pendingAnchorDelta = 0
                _setContentY(messageViewport.contentY + anchorDelta, false)
            }
        })
    }

    function _cacheSlotHeight(slot, measuredHeight) {
        if (!slot || !isFinite(measuredHeight) || measuredHeight <= 0) return
        var previousHeight = slot._measuredHeight
        var nextHeight = Math.max(_minimumMessageHeight, measuredHeight)
        var heightDelta = nextHeight - previousHeight
        var slotWasAboveViewport = slot.y + previousHeight <= messageViewport.contentY
        if (Math.abs(heightDelta) < _heightChangeTolerance
                && slot._measuredKey === slot._measurementKey) return

        slot._measuredHeight = nextHeight
        slot._measuredKey = slot._measurementKey
        _scheduleSlotLayout()
        if (_followBottom) {
            _scheduleScrollToBottom()
        } else if (slotWasAboveViewport
                && Math.abs(heightDelta) >= _heightChangeTolerance) {
            _pendingAnchorDelta += heightDelta
        }
    }

    // ==================== Public Methods 公开方法 ====================
    function appendMessage(role, content, timestamp) {
        chatModel.append({
            role: role || "assistant",
            content: content || "",
            reasoning: "",
            timestamp: timestamp || ""
        })
        if (_followBottom) _scheduleScrollToBottom()
    }

    function appendReasoningToLast(chunk) {
        if (chatModel.count === 0) return
        var index = chatModel.count - 1
        var previousReasoning = chatModel.get(index).reasoning || ""
        chatModel.setProperty(index, "reasoning", previousReasoning + chunk)
        if (_followBottom) _scheduleScrollToBottom()
    }

    function updateLastContent(text) {
        if (chatModel.count === 0) return
        chatModel.setProperty(chatModel.count - 1, "content", text)
        if (_followBottom) _scheduleScrollToBottom()
    }

    function setLastContent(text) {
        updateLastContent(text)
    }

    function appendToLast(chunk) {
        if (chatModel.count === 0) return
        var index = chatModel.count - 1
        var previousContent = chatModel.get(index).content || ""
        chatModel.setProperty(index, "content", previousContent + chunk)
        if (_followBottom) _scheduleScrollToBottom()
    }

    function clear() {
        chatModel.clear()
        _pendingAnchorDelta = 0
        messageColumn.height = 0
        _setContentY(0, true)
    }

    function scrollToEnd() {
        _followBottom = true
        _scheduleScrollToBottom()
    }

    function getLastRole() {
        if (chatModel.count === 0) return ""
        return chatModel.get(chatModel.count - 1).role
    }

    // ==================== Content 内容 ====================
    ListModel {
        id: chatModel
    }

    Flickable {
        id: messageViewport

        objectName: "chatMessageViewport"
        anchors.fill: parent
        contentWidth: width
        contentHeight: messageColumn.height
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        interactive: false

        onContentYChanged: {
            if (!control._adjustingScroll) control._followBottom = control._isAtBottom
        }
        onContentHeightChanged: {
            if (control._followBottom) control._scheduleScrollToBottom()
        }

        Item {
            id: messageColumn

            objectName: "chatMessageContent"
            width: messageViewport.width

            Repeater {
                id: messageRepeater

                model: chatModel
                onItemAdded: control._scheduleSlotLayout()

                delegate: Loader {
                    id: messageSlot

                    required property int index
                    required property string role
                    required property string content
                    required property string reasoning
                    required property string timestamp
                    property bool _layoutReady: false
                    property bool _reasoningExpanded: true
                    property bool _userToggledReasoning: false
                    property real _measuredHeight: control._minimumMessageHeight
                    property string _measuredKey: ""
                    readonly property string _measurementKey: [
                        width,
                        role,
                        content,
                        reasoning,
                        timestamp,
                        control.maxBubbleWidth,
                        control.assistantAvatarText,
                        String(control.assistantAvatarSource),
                        control.showAssistantAvatar,
                        _reasoningExpanded,
                        _userToggledReasoning,
                        Enums.fontFamily
                    ].join("\u001f")
                    readonly property bool _inLoadRange:
                        y + height >= messageViewport.contentY - control._loadMargin
                        && y <= messageViewport.contentY + messageViewport.height
                            + control._loadMargin

                    function _measureLoadedBubble() {
                        if (item) control._cacheSlotHeight(messageSlot, item.implicitHeight)
                    }

                    width: messageColumn.width
                    height: _measuredHeight
                    active: _layoutReady && _inLoadRange
                    asynchronous: true

                    onContentChanged: {
                        if (content !== "" && !_userToggledReasoning) {
                            _reasoningExpanded = false
                        }
                    }
                    on_MeasurementKeyChanged: {
                        if (item) Qt.callLater(_measureLoadedBubble)
                    }
                    onLoaded: _measureLoadedBubble()

                    sourceComponent: ChatBubble {
                        role: messageSlot.role
                        content: messageSlot.content
                        reasoning: messageSlot.reasoning
                        timestamp: messageSlot.timestamp
                        maxBubbleWidth: control.maxBubbleWidth
                        avatarText: control.assistantAvatarText
                        avatarSource: control.assistantAvatarSource
                        showAvatar: control.showAssistantAvatar
                        _reasoningExpanded: messageSlot._reasoningExpanded
                        _userToggledReasoning: messageSlot._userToggledReasoning

                        onImplicitHeightChanged:
                            control._cacheSlotHeight(messageSlot, implicitHeight)
                        on_ReasoningExpandedChanged:
                            messageSlot._reasoningExpanded = _reasoningExpanded
                        on_UserToggledReasoningChanged:
                            messageSlot._userToggledReasoning = _userToggledReasoning
                    }
                }
            }
        }
    }

    SmoothScrollHelper {
        id: scrollHelper

        target: messageViewport
        orientation: Qt.Vertical
        handleWheel: true
    }

    ScrollBar {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.rightMargin: Enums.spacing.xxs
        target: messageViewport
        scrollHelper: scrollHelper
        orientation: Qt.Vertical
        barWidth: Enums.spacing.s
        z: Enums.zIndex.controlsAbove
    }
}
