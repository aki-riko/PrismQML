// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// NotificationStackManager - Stack management for notifications 通知堆叠管理
// Handles positioning and stacking of InfoBar/Toast 处理InfoBar/Toast的定位和堆叠
QtObject {
    id: stackManager
    
    // ==================== Readonly State 只读状态 ====================
    // Use shared position constants 使用共享位置常量
    readonly property int posTopLeft: Enums.notification.posTopLeft
    readonly property int posTop: Enums.notification.posTop
    readonly property int posTopRight: Enums.notification.posTopRight
    readonly property int posLeft: Enums.notification.posLeft
    readonly property int posCenter: Enums.notification.posCenter
    readonly property int posRight: Enums.notification.posRight
    readonly property int posBottomLeft: Enums.notification.posBottomLeft
    readonly property int posBottom: Enums.notification.posBottom
    readonly property int posBottomRight: Enums.notification.posBottomRight

    // ==================== Internal Props 内部属性 ====================
    // Notification stack gap Use shared layout config 通知堆叠间距，使用共享布局配置
    readonly property int _infoBarStackGap: Enums.notification.layout.stackGapLarge
    readonly property int _compactStackGap: Enums.spacing.m
    property var _stacks: null
    property var _desktopStacks: null

    // ==================== Internal Methods 内部方法 ====================
    // Validate position 验证位置有效性
    function _isValidPosition(position) {
        return position !== undefined && position !== null && position >= 0 && position <= 8
    }

    function _isSameScreen(first, second) {
        if (first === second) return true
        if (!first || !second) return false
        return first.name === second.name
    }

    // Window stack methods 窗口内堆叠方法
    function addToStack(item, position) {
        if (!_stacks || !_isValidPosition(position)) {
            console.warn("NotificationStackManager: Invalid position or stacks not initialized:", position)
            return
        }
        _stacks[position].push(item)
        item.heightChanged.connect(function() {
            stackManager.repositionStack(position)
        })
    }

    function removeFromStack(item, position) {
        if (!_stacks || !_isValidPosition(position)) return
        var stack = _stacks[position]
        if (!stack) return
        var index = stack.indexOf(item)
        if (index >= 0) {
            stack.splice(index, 1)
            repositionStack(position)
        }
    }

    function repositionStack(position) {
        if (!_stacks || !_isValidPosition(position)) return
        var stack = _stacks[position]
        if (!stack) return

        for (var i = 0; i < stack.length; i++) {
            var item = stack[i]
            var offset = calculateOffset(stack, i, position)
            // Use animator's updatePosition for smooth reposition 使用动画器的 updatePosition 实现平滑补位
            if (item.animator) {
                item.animator.updatePosition(offset)
            }
        }
    }

    function _stackInset(item, propertyName) {
        if (!item) return 0
        var value = item[propertyName]
        return value === undefined || value === null ? 0 : value
    }

    function _visualStackAdvance(item, nextItem, position, gap) {
        var inset = Enums.notification.isBottom(position)
            ? _stackInset(item, "_stackTopInset")
                + _stackInset(nextItem, "_stackBottomInset")
            : _stackInset(item, "_stackBottomInset")
                + _stackInset(nextItem, "_stackTopInset")
        return item.height + gap - inset
    }

    function calculateOffset(stack, index, position) {
        if (!stack) return 0
        var offset = 0
        for (var i = 0; i < index; i++) {
            var item = stack[i]
            var nextItem = stack[i + 1]
            var gap = (item.desktopMode === undefined) ? _infoBarStackGap : _compactStackGap
            offset += _visualStackAdvance(item, nextItem, position, gap)
        }
        return offset
    }

    // Desktop stack methods 桌面堆叠方法
    function addToDesktopStack(overlay, position) {
        if (!_desktopStacks || !_isValidPosition(position)) {
            console.warn("NotificationStackManager: Invalid position for desktop stack:", position)
            return
        }
        _desktopStacks[position].push(overlay)
        overlay.contentHeightChanged.connect(function() {
            stackManager.repositionDesktopStack(position)
        })
        overlay.screenChanged.connect(function() {
            stackManager.repositionDesktopStack(position)
        })
        repositionDesktopStack(position)
    }

    function removeFromDesktopStack(overlay, position) {
        if (!_desktopStacks || !_isValidPosition(position)) return
        var stack = _desktopStacks[position]
        if (!stack) return
        var index = stack.indexOf(overlay)
        if (index >= 0) {
            stack.splice(index, 1)
            repositionDesktopStack(position)
        }
    }

    function repositionDesktopStack(position) {
        if (!_desktopStacks || !_isValidPosition(position)) return
        var stack = _desktopStacks[position]
        if (!stack) return
        for (var i = 0; i < stack.length; i++) {
            var offset = calculateDesktopOffset(stack, i, stack[i], position)
            stack[i].stackOffset = offset
            stack[i].updatePosition()
        }
    }

    function _nextDesktopItem(stack, currentIndex, targetIndex, targetScreen, targetOverlay) {
        for (var i = currentIndex + 1; i < targetIndex; i++) {
            if (!targetScreen || _isSameScreen(stack[i].screen, targetScreen)) return stack[i]
        }
        return targetOverlay
    }

    function calculateDesktopOffset(stack, index, targetOverlay, position) {
        if (!stack) return 0
        var offset = 0
        var targetScreen = targetOverlay ? targetOverlay.screen : null
        for (var i = 0; i < index; i++) {
            if (targetScreen && !_isSameScreen(stack[i].screen, targetScreen)) continue
            var nextItem = _nextDesktopItem(
                stack, i, index, targetScreen, targetOverlay
            )
            offset += _visualStackAdvance(
                stack[i], nextItem, position, _compactStackGap
            )
        }
        return offset
    }

    function closeAllDesktopNotifications() {
        if (!_desktopStacks) return
        for (var pos = 0; pos <= 8; pos++) {
            var stack = _desktopStacks[pos]
            if (!stack) continue
            while (stack.length > 0) {
                var overlay = stack.pop()
                if (overlay) {
                    if (overlay.notificationItem) {
                        overlay.notificationItem.destroy()
                    }
                    overlay.visible = false
                    overlay.destroy()
                }
            }
        }
    }

    // Position helper 位置辅助
    // Now only calculates and passes stackOffset to animator 现在只计算并传递stackOffset给动画器
    function setPosition(item, parent, position, extraMargin) {
        if (!_stacks || !_isValidPosition(position)) return
        var stack = _stacks[position]
        if (!stack) return
        var stackOffset = calculateOffset(stack, stack.length - 1, position)
        // Pass stackOffset to animator, animator handles actual positioning 传递stackOffset给动画器，动画器处理实际定位
        if (item.animator) {
            item.animator.stackOffset = stackOffset
        }
    }

    // Utility method 工具方法
    function randomPosition() {
        var positions = [
            posTopLeft, posTop, posTopRight,
            posLeft, posCenter, posRight,
            posBottomLeft, posBottom, posBottomRight
        ]
        return positions[Math.floor(Math.random() * positions.length)]
    }

    // Initialize stacks on component completion 组件完成时初始化堆栈
    Component.onCompleted: {
        _stacks = { 0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [] }
        _desktopStacks = { 0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [] }
    }
}
