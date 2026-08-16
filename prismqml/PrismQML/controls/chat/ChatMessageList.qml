// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../.."
import "."
import "_internal" as ChatInternal
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
 *   showScrollBar: bool
 *   scrollBarWidth: int
 */
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int maxBubbleWidth: Enums.controlSize.chatContentMaxWidth
    property string assistantAvatarText: ""
    property url assistantAvatarSource: ""
    property bool showAssistantAvatar: true
    property bool showScrollBar: true
    property int scrollBarWidth: Enums.controlSize.scrollBarWidth

    // ==================== Internal Props 内部属性 ====================
    property bool _followBottom: true
    property bool _adjustingScroll: false
    property bool _scrollPending: false
    property bool _layoutPending: false
    property bool _rangeUpdatePending: false
    property real _pendingAnchorDelta: 0
    property int _layoutStartIndex: -1
    property int _lastLayoutStartIndex: -1
    property int _firstLoadIndex: -1
    property int _lastLoadIndex: -1
    property alias messageViewport: messageContent.viewport
    property alias messageColumn: messageContent.contentColumn
    property alias messageRepeater: messageContent.repeater

    // ==================== Readonly State 只读状态 ====================
    readonly property int messageCount: chatModel.count
    readonly property alias _needsScrollBar: scrollViewportState.needsVertical
    readonly property alias _reserveScrollBarGutter:
        scrollViewportState.reserveVerticalGutter
    readonly property real _scrollBarGutter:
        Math.max(0, scrollBarWidth) + Enums.spacing.xs
    readonly property real _loadMargin: Math.max(0, messageViewport.height)
    readonly property real _minimumMessageHeight:
        Enums.spacing.l * 2 + Enums.spacing.m + Enums.spacing.xl
    readonly property real _bottomTolerance: Enums.spacing.l * 2
    readonly property real _heightChangeTolerance: Enums.border.thin / 2
    readonly property bool _isAtBottom:
        messageViewport.contentY + messageViewport.height
        >= messageViewport.contentHeight - _bottomTolerance

    // ==================== Internal Methods 内部方法 ====================
    function _scheduleScrollBarUpdate() {
        if (scrollViewportState) scrollViewportState.invalidate()
    }

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
        scrollToBottomTimer.start()
    }

    function _scheduleSlotLayout(startIndex) {
        var count = messageRepeater.count
        var requestedStart = typeof startIndex === "number" && isFinite(startIndex)
            ? Math.max(0, Math.min(count, Math.floor(startIndex))) : 0
        if (_layoutStartIndex < 0 || requestedStart < _layoutStartIndex) {
            _layoutStartIndex = requestedStart
        }
        if (_layoutPending) return
        _layoutPending = true
        slotLayoutTimer.start()
    }

    function _findFirstLoadIndex(topY) {
        var low = 0
        var high = messageRepeater.count - 1
        var result = messageRepeater.count
        while (low <= high) {
            var middle = Math.floor((low + high) / 2)
            var slot = messageRepeater.itemAt(middle)
            if (slot && slot.y + slot.height >= topY) {
                result = middle
                high = middle - 1
            } else {
                low = middle + 1
            }
        }
        return result
    }

    function _findLastLoadIndex(bottomY) {
        var low = 0
        var high = messageRepeater.count - 1
        var result = -1
        while (low <= high) {
            var middle = Math.floor((low + high) / 2)
            var slot = messageRepeater.itemAt(middle)
            if (slot && slot.y <= bottomY) {
                result = middle
                low = middle + 1
            } else {
                high = middle - 1
            }
        }
        return result
    }

    function _applyLoadRange(firstIndex, lastIndex) {
        for (var oldIndex = Math.max(0, _firstLoadIndex);
                oldIndex <= _lastLoadIndex; oldIndex++) {
            if (oldIndex >= firstIndex && oldIndex <= lastIndex) continue
            var oldSlot = messageRepeater.itemAt(oldIndex)
            if (oldSlot) oldSlot._inLoadRange = false
        }
        for (var newIndex = Math.max(0, firstIndex);
                newIndex <= lastIndex; newIndex++) {
            var newSlot = messageRepeater.itemAt(newIndex)
            if (newSlot) newSlot._inLoadRange = true
        }
        _firstLoadIndex = firstIndex
        _lastLoadIndex = lastIndex
    }

    function _scheduleLoadRangeUpdate() {
        if (_rangeUpdatePending) return
        _rangeUpdatePending = true
        loadRangeTimer.start()
    }

    function _scheduleSlotMeasurement(slot) {
        if (slot) slot._scheduleMeasurement()
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
        _scheduleSlotLayout(slot.index)
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
        _scheduleScrollBarUpdate()
        if (_followBottom) _scheduleScrollToBottom()
    }

    function appendReasoningToLast(chunk) {
        if (chatModel.count === 0) return
        var index = chatModel.count - 1
        var previousReasoning = chatModel.get(index).reasoning || ""
        chatModel.setProperty(index, "reasoning", previousReasoning + chunk)
        _scheduleScrollBarUpdate()
        if (_followBottom) _scheduleScrollToBottom()
    }

    function updateLastContent(text) {
        if (chatModel.count === 0) return
        chatModel.setProperty(chatModel.count - 1, "content", text)
        _scheduleScrollBarUpdate()
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
        _scheduleScrollBarUpdate()
        if (_followBottom) _scheduleScrollToBottom()
    }

    function clear() {
        chatModel.clear()
        _pendingAnchorDelta = 0
        _layoutStartIndex = -1
        _lastLayoutStartIndex = -1
        _firstLoadIndex = -1
        _lastLoadIndex = -1
        messageColumn.height = 0
        _setContentY(0, true)
        _scheduleScrollBarUpdate()
    }

    function scrollToEnd() {
        _followBottom = true
        _scheduleScrollToBottom()
    }

    function getLastRole() {
        if (chatModel.count === 0) return ""
        return chatModel.get(chatModel.count - 1).role
    }

    onShowScrollBarChanged: _scheduleScrollBarUpdate()
    onScrollBarWidthChanged: _scheduleScrollBarUpdate()
    onWidthChanged: _scheduleScrollBarUpdate()
    onHeightChanged: _scheduleScrollBarUpdate()
    Component.onCompleted: _scheduleScrollBarUpdate()

    // ==================== Deferred Work 延迟任务 ====================
    ChatInternal.ChatMessageListScrollToBottomTimer {
        id: scrollToBottomTimer
        host: control
    }

    Timer {
        id: slotLayoutTimer

        interval: 0
        repeat: false
        onTriggered: {
            control._layoutPending = false
            var slotCount = messageRepeater.count
            var layoutStart = Math.max(0, Math.min(slotCount, control._layoutStartIndex))
            control._layoutStartIndex = -1
            var nextY = 0
            if (layoutStart > 0) {
                var previousSlot = messageRepeater.itemAt(layoutStart - 1)
                if (previousSlot && previousSlot._layoutReady) {
                    nextY = previousSlot.y + previousSlot.height + Enums.spacing.xs
                } else {
                    layoutStart = 0
                }
            }
            control._lastLayoutStartIndex = layoutStart
            for (var i = layoutStart; i < slotCount; i++) {
                var slot = messageRepeater.itemAt(i)
                if (!slot) continue
                slot.y = nextY
                nextY += slot.height
                if (i + 1 < slotCount) nextY += Enums.spacing.xs
                if (!slot._layoutReady) slot._layoutReady = true
            }
            messageColumn.height = nextY
            control._scheduleLoadRangeUpdate()
            if (control._followBottom) {
                control._pendingAnchorDelta = 0
                control._scheduleScrollToBottom()
            } else if (Math.abs(control._pendingAnchorDelta)
                    >= control._heightChangeTolerance) {
                var anchorDelta = control._pendingAnchorDelta
                control._pendingAnchorDelta = 0
                control._setContentY(messageViewport.contentY + anchorDelta, false)
            }
        }
    }

    Timer {
        id: loadRangeTimer

        interval: 0
        repeat: false
        onTriggered: {
            control._rangeUpdatePending = false
            var count = messageRepeater.count
            if (count === 0) {
                control._applyLoadRange(-1, -1)
                return
            }
            var finalSlot = messageRepeater.itemAt(count - 1)
            if (!finalSlot || !finalSlot._layoutReady) {
                control._scheduleSlotLayout(0)
                return
            }
            var topY = messageViewport.contentY - control._loadMargin
            var bottomY = messageViewport.contentY + messageViewport.height
                + control._loadMargin
            var firstIndex = control._findFirstLoadIndex(topY)
            var lastIndex = control._findLastLoadIndex(bottomY)
            if (firstIndex > lastIndex) {
                control._applyLoadRange(-1, -1)
                return
            }
            control._applyLoadRange(firstIndex, lastIndex)
        }
    }

    // ==================== Content 内容 ====================
    ListModel {
        id: chatModel
    }

    ChatInternal.ChatMessageViewport {
        id: messageContent

        chatControl: control
        messageModel: chatModel
    }

    ScrollViewportState {
        id: scrollViewportState
        target: messageViewport
        scrollBarsEnabled: control.showScrollBar
        verticalEnabled: true
        itemCount: control.messageCount
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
        barWidth: Math.max(0, control.scrollBarWidth)
        visible: control._needsScrollBar
        z: Enums.zIndex.controlsAbove
    }
}
