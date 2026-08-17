// ChatMessageViewport - Virtualized message viewport 消息虚拟化视口
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."

// ChatMessageViewport - Owns the flickable slot tree 承载滚动与消息占位树
Flickable {
    id: messageViewport

    // ==================== Required Props 必需属性 ====================
    required property var chatControl
    required property var messageModel

    // ==================== Public Props 公开属性 ====================
    property alias viewport: messageViewport
    property alias contentColumn: messageColumn
    property alias repeater: messageRepeater

    // ==================== Internal Props 内部属性 ====================
    property var _hostControl: null

    anchors.fill: parent
    objectName: "chatMessageViewport"
    anchors.rightMargin: _hostControl
        ? (_hostControl._reserveScrollBarGutter
            ? Math.min(_hostControl._scrollBarGutter, Math.max(0, parent.width)) : 0)
        : 0
    contentWidth: width
    contentHeight: messageColumn.height
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    interactive: false

    onContentYChanged: {
        if (_hostControl && !_hostControl._adjustingScroll)
            _hostControl._followBottom = _hostControl._isAtBottom
        if (_hostControl) _hostControl._scheduleLoadRangeUpdate()
    }
    onContentHeightChanged: {
        if (_hostControl && _hostControl._followBottom)
            _hostControl._scheduleScrollToBottom()
    }
    onHeightChanged: if (_hostControl) _hostControl._scheduleLoadRangeUpdate()

    Component.onCompleted: {
        _hostControl = chatControl
        _hostControl._scheduleSlotLayout(0)
    }

    // ==================== Content 内容 ====================
    Item {
        id: messageColumn

        objectName: "chatMessageContent"
        width: messageViewport.width

        Repeater {
            id: messageRepeater

            model: messageModel
            onItemAdded: (index, item) => {
                if (_hostControl) _hostControl._scheduleSlotLayout(index)
            }

            delegate: ChatMessageSlot {
                host: messageViewport._hostControl
                // Qualify the outer column to avoid the delegate's same-named property.
                // 明确限定外层列，避免解析为委托自身的同名属性。
                messageColumn: messageViewport.contentColumn
            }
        }
    }
}
