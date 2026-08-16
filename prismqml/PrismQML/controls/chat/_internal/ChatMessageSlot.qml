// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "." as ChatInternal

// ChatMessageSlot - Virtualized chat message loader 虚拟化聊天消息加载器
// Keeps message measurement and bubble construction outside the list coordinator 将测量与气泡装配移出列表编排器
Loader {
    id: slot

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property var messageColumn
    required property int index
    required property string role
    required property string content
    required property string reasoning
    required property string timestamp

    // ==================== Internal Props 内部属性 ====================
    property bool _layoutReady: false
    property bool _reasoningExpanded: true
    property bool _userToggledReasoning: false
    property real _measuredHeight: host ? host._minimumMessageHeight : 0
    property string _measuredKey: ""
    readonly property string _measurementKey: [
        width,
        role,
        content,
        reasoning,
        timestamp,
        host.maxBubbleWidth,
        host.assistantAvatarText,
        String(host.assistantAvatarSource),
        host.showAssistantAvatar,
        _reasoningExpanded,
        _userToggledReasoning,
        Enums.fontFamily
    ].join("\u001f")
    property bool _inLoadRange: false

    // ==================== Internal Methods 内部方法 ====================
    function _scheduleMeasurement() {
        slotMeasurementTimer.start()
    }

    // ==================== Size 尺寸 ====================
    width: messageColumn ? messageColumn.width : 0
    height: _measuredHeight
    active: _layoutReady && _inLoadRange
    asynchronous: true

    onContentChanged: {
        if (content !== "" && !_userToggledReasoning) {
            _reasoningExpanded = false
        }
    }
    on_MeasurementKeyChanged: {
        if (item && host) host._scheduleSlotMeasurement(slot)
    }
    onLoaded: if (host) host._scheduleSlotMeasurement(slot)

    // ==================== Content 内容 ====================
    ChatInternal.ChatMessageSlotMeasurementTimer {
        id: slotMeasurementTimer
        targetSlot: slot
        host: slot.host
    }

    sourceComponent: ChatBubble {
        role: slot.role
        content: slot.content
        reasoning: slot.reasoning
        timestamp: slot.timestamp
        maxBubbleWidth: host.maxBubbleWidth
        avatarText: host.assistantAvatarText
        avatarSource: host.assistantAvatarSource
        showAvatar: host.showAssistantAvatar
        _reasoningExpanded: slot._reasoningExpanded
        _userToggledReasoning: slot._userToggledReasoning

        onImplicitHeightChanged:
            host._cacheSlotHeight(slot, implicitHeight)
        on_ReasoningExpandedChanged:
            slot._reasoningExpanded = _reasoningExpanded
        on_UserToggledReasoningChanged:
            slot._userToggledReasoning = _userToggledReasoning
    }
}
