// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../.."
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖
import QtQuick.Window  // 置于库import后:去前缀后保原生Window不被库覆盖

// OverlayDialogCore - Base class for overlay dialogs 覆盖式对话框基类
// Provides common overlay functionality for MaskedDialog and DialogBoxCore 为 MaskedDialog 和 DialogBoxCore 提供共同的覆盖功能

// 
// Features 功能:
// - overlayTarget property for component-level overlay 组件级别覆盖
// - Wheel event blocking 滚轮事件拦截
// - Parent restoration after close 关闭后恢复父组件
// - Mask layer with click handling 遮罩层点击处理
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property bool dismissOnScrimClick: false  // Close when overlay scrim is clicked 点击遮罩关闭
    property bool draggable: false              // Allow drag dialog 允许拖拽
    
    // Overlay target 覆盖目标
    // null = stay with current parent (component-level overlay) null = 保持当前父组件（组件级别覆盖）

    // Set to Window.window.contentItem for window-level overlay 设置为 Window.window.contentItem 以实现窗口级别覆盖

    property Item overlayTarget: null
    
    // Mask color 遮罩颜色
    property color maskColor: Enums.stateColor.maskHeavy
    
    // ==================== Internal State 内部状态 ====================
    property bool _isOpen: false
    property bool _isClosing: false
    property point _dragPos: Qt.point(0, 0)
    property Item _originalParent: null  // Original parent before reparenting 重新父化前的原始父组件
    
    // ==================== Signals 信号 ====================
    signal accepted()
    signal rejected()
    signal closed()
    
    // ==================== Layout 布局 ====================
    anchors.fill: parent
    z: Enums.zIndex.modal
    visible: _isOpen || _isClosing
    
    // Ensure anchors update when parent changes (e.g. via Python setParentItem) 确保 parent 变化时 anchors 正确更新（如通过 Python setParentItem）

    onParentChanged: {
        if (parent) {
            // Force anchors reset to ensure size updates 强制重置 anchors 确保尺寸更新

            anchors.fill = undefined
            anchors.fill = parent
            // Force immediate size update from parent 强制立即从parent更新尺寸
            if (parent.width > 0) control.width = parent.width
            if (parent.height > 0) control.height = parent.height
        }
    }

    // ==================== Public Methods 公开方法 ====================

    // Open dialog 打开对话框
    function open() {
        // Save original parent 保存原始父组件
        if (!_originalParent) {
            _originalParent = control.parent
        }

        // Determine overlay target 确定覆盖目标
        var target = _resolveOverlayTarget()
        if (target && target !== control.parent) {
            control.parent = target
        }

        _isOpen = true
    }

    // Resolve overlay target 解析覆盖目标
    function _resolveOverlayTarget() {
        // If overlayTarget is specified, use it 如果指定了overlayTarget则使用它
        if (overlayTarget) {
            return overlayTarget
        }

        // ✅ 2026-05-15: 默认升到 Window 级覆盖,避免对话框被父组件 (ScrollArea / 局部布局) 限制位置
        // 调用方若需组件级覆盖,显式设 overlayTarget 即可
        if (Window.window && Window.window.contentItem) {
            return Window.window.contentItem
        }

        return null
    }

    // Accept and close 接受并关闭
    function accept() {
        if (!_isOpen) return
        _isClosing = true
        _isOpen = false
        accepted()
        _restoreParentTimer.start()
    }

    // Reject and close 拒绝并关闭
    function reject() {
        if (!_isOpen) return
        _isClosing = true
        _isOpen = false
        rejected()
        _restoreParentTimer.start()
    }

    // Close dialog (alias for reject) 关闭对话框
    function close() {
        if (!_isOpen) return
        _isClosing = true
        _isOpen = false
        closed()
        _restoreParentTimer.start()
    }

    // Restore state after close 关闭后恢复状态
    // 不再 reparent 回 _originalParent — nested OverlayDialog 场景下,外层 dialog 自身
    // 已 reparent 到 contentItem, 内层 reject 后若 reparent 回 bodyLayout (外层 dialog 的子 Item),
    // onParentChanged 触发的 anchors 重设会让 childrenRect 短暂归零, 进而让外层 dialogBody 视觉崩坏。
    // 第二次 open 时 _resolveOverlayTarget 会判断 target === control.parent 跳过 reparent,
    // 所以 parent 留在 contentItem 不影响后续 open 的正确性。
    function _restoreParent() {
        _isClosing = false
    }

    // Also update size when parent size changes 当parent尺寸变化时也更新
    Connections {
        target: control.parent
        function onWidthChanged() { if (control.parent) control.width = control.parent.width }
        function onHeightChanged() { if (control.parent) control.height = control.parent.height }
    }
    
    // ==================== Mask Layer 遮罩层 ====================
    Rectangle {
        id: windowMask
        anchors.fill: parent
        color: control.maskColor
        
        // Fade animation 淡入淡出动画
        opacity: control._isOpen ? 1 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: control._isClosing ? Enums.duration.fast : Enums.duration.medium
                easing.type: control._isClosing ? Easing.Linear : Easing.InSine
            }
        }
        
        MouseArea {
            anchors.fill: parent
            // 拦截 hover/wheel/click 防止穿透到下层 ListView/CommandBar 等
            // (默认 hoverEnabled=false, 不接 hover 时下层 hover 高亮仍可见)
            hoverEnabled: true
            acceptedButtons: Qt.AllButtons
            onWheel: (wheel) => wheel.accepted = true
            onClicked: {
                if (control.dismissOnScrimClick) {
                    control.reject()
                }
            }
        }
    }

    // Timer to restore parent after close animation 关闭动画后恢复父组件的定时器
    Timer {
        id: _restoreParentTimer
        interval: Enums.duration.medium + Enums.spacing.xl
        onTriggered: control._restoreParent()
    }
    
    // ==================== Utility Methods 工具方法 ====================
}