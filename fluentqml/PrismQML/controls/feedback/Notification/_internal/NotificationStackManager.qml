// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."

// NotificationStackManager - Stack management for notifications 通知堆叠管理
// Handles positioning and stacking of InfoBar/Toast 处理InfoBar/Toast的定位和堆叠
QtObject {
    id: stackManager
    
    // ==================== Position Enum 位置枚举 ====================
    // Use shared position constants 使用共享位置常量
    readonly property int posTopLeft: Enums.notification.posTopLeft
    readonly property int posTop: Enums.notification.posTop
    readonly property int posTopRight: Enums.notification.posTopRight
    readonly property int posBottomLeft: Enums.notification.posBottomLeft
    readonly property int posBottom: Enums.notification.posBottom
    readonly property int posBottomRight: Enums.notification.posBottomRight
    
    // ==================== Stacking 堆叠管理 ====================
    property var _stacks: null
    property var _desktopStacks: null
    

    // Initialize stacks on component completion 组件完成时初始化堆栈
    Component.onCompleted: {
        _stacks = { 0: [], 1: [], 2: [], 3: [], 4: [], 5: [] }
        _desktopStacks = { 0: [], 1: [], 2: [], 3: [], 4: [], 5: [] }
    }

    // Notification stack gap Use shared layout config 通知堆叠间距，使用共享布局配置
    readonly property int _infoBarStackGap: Enums.notification.layout.stackGapLarge
    readonly property int _stackGap: Enums.notification.layout.stackGapSmall

    // Validate position 验证位置有效性
    function _isValidPosition(position) {
        return position !== undefined && position !== null && position >= 0 && position <= 5
    }

    // ==================== Window Stack Methods 窗口内堆叠方法 ====================
    function addToStack(item, position) {
        if (!_stacks || !_isValidPosition(position)) {
            console.warn("NotificationStackManager: Invalid position or stacks not initialized:", position)
            return
        }
        _stacks[position].push(item)
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
            var offset = calculateOffset(stack, i)
            // Use animator's updatePosition for smooth reposition 使用动画器的 updatePosition 实现平滑补位
            if (item.animator) {
                item.animator.updatePosition(offset)
            }
        }
    }

    function calculateOffset(stack, index) {
        if (!stack) return 0
        var offset = 0
        for (var i = 0; i < index; i++) {
            var item = stack[i]
            var gap = (item.desktopMode === undefined) ? _infoBarStackGap : _stackGap
            offset += item.height + gap
        }
        return offset
    }

    // ==================== Desktop Stack Methods 桌面堆叠方法 ====================
    function addToDesktopStack(overlay, position) {
        if (!_desktopStacks || !_isValidPosition(position)) {
            console.warn("NotificationStackManager: Invalid position for desktop stack:", position)
            return
        }
        _desktopStacks[position].push(overlay)
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
            var offset = calculateDesktopOffset(stack, i)
            stack[i].stackOffset = offset
            stack[i].updatePosition()
        }
    }

    function calculateDesktopOffset(stack, index) {
        if (!stack) return 0
        var offset = 0
        for (var i = 0; i < index; i++) {
            offset += stack[i].contentHeight + _stackGap
        }
        return offset
    }

    function getDesktopStackOffset(position) {
        if (!_desktopStacks || !_isValidPosition(position)) return 0
        var stack = _desktopStacks[position]
        if (!stack) return 0
        return calculateDesktopOffset(stack, stack.length)
    }

    function closeAllDesktopNotifications() {
        if (!_desktopStacks) return
        for (var pos = 0; pos <= 5; pos++) {
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

    // ==================== Position Helper 位置辅助 ====================
    // Now only calculates and passes stackOffset to animator 现在只计算并传递stackOffset给动画器
    function setPosition(item, parent, position, extraMargin) {
        if (!_stacks || !_isValidPosition(position)) return
        var stack = _stacks[position]
        if (!stack) return
        var stackOffset = calculateOffset(stack, stack.length - 1)
        // Pass stackOffset to animator, animator handles actual positioning 传递stackOffset给动画器，动画器处理实际定位
        if (item.animator) {
            item.animator.stackOffset = stackOffset
        }
    }

    // ==================== Utility 工具方法 ====================
    function randomPosition() {
        var positions = [posTopLeft, posTop, posTopRight, posBottomLeft, posBottom, posBottomRight]
        return positions[Math.floor(Math.random() * positions.length)]
    }
}
