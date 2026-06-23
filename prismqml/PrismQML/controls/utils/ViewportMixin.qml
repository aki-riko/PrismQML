// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// ViewportMixin - Viewport visibility detection mixin 可视区域检测混入组件
// Used to optimize scroll performance, pauses animations when not visible 用于优化滚动性能，不可见时暂停动画

// Usage: ViewportMixin { id: viewport; target: control }
// Then use: viewport.isInViewport to control animations
QtObject {
    id: mixin
    
    // ==================== Required 必需属性 ====================
    required property Item target  // 要检测的目标组件
    
    // ==================== Output 输出属性 ====================
    property bool isInViewport: true  // 默认可见
    property bool ready: false  // 初始化完成标志
    
    // ==================== Internal 内部属性 ====================
    property var _flickableAncestor: null
    
    // Find Flickable ancestor by checking contentY property 向上查找 Flickable 祖先
    function _findFlickable() {
        if (!target) return null
        var p = target.parent
        while (p) {
            // Check for Flickable characteristic properties 检查是否有 Flickable 特征属性
            if (p.contentY !== undefined && p.contentHeight !== undefined && p.contentItem !== undefined) {
                return p
            }
            p = p.parent
        }
        return null
    }
    
    // Calculate if target is in visible viewport 计算是否在可视区域
    function _updateViewport() {
        try {
            // No Flickable found, keep default true (always animate) 找不到 Flickable，保持默认 true
            if (!_flickableAncestor) {
                isInViewport = true
                return
            }
            if (!target || !target.visible) {
                isInViewport = false
                return
            }
            // Check if contentItem exists 检查contentItem是否存在
            if (!_flickableAncestor.contentItem) {
                isInViewport = true
                return
            }
            // Check if height is valid 检查高度是否有效
            if (_flickableAncestor.height <= 0) {
                isInViewport = true
                return
            }
            var pos = target.mapToItem(_flickableAncestor.contentItem, 0, 0)
            var viewTop = _flickableAncestor.contentY
            var viewBottom = viewTop + _flickableAncestor.height
            // Buffer to avoid edge flickering 缓冲区避免边缘闪烁
            var buffer = target.height
            isInViewport = (pos.y + target.height + buffer > viewTop) && (pos.y - buffer < viewBottom)
        } catch (e) {
            // Fallback to visible if any error occurs 发生任何错误时回退到可见
            isInViewport = true
        }
    }
    
    // Connect initialization signals 初始化连接
    function _init() {
        _flickableAncestor = _findFlickable()
        if (_flickableAncestor) {
            _flickableAncestor.contentYChanged.connect(_updateViewport)
            _flickableAncestor.heightChanged.connect(_updateViewport)
            // Listen to contentItem size changes (triggered when layout completes) 监听 contentItem 尺寸变化（布局完成时触发）
            _flickableAncestor.contentItem.heightChanged.connect(_updateViewport)
        }
        _updateViewport()
        ready = true  // 标记初始化完成
    }
    
    // Delayed initialization to ensure component tree is built 延迟初始化，确保组件树构建完成 // Timer delay is more reliable than Qt.callLater, ensures layout completion 使用 Timer 延迟比 Qt.callLater 更可靠
    Component.onCompleted: initTimer.start()
    
    property Timer initTimer: Timer {
        interval: 50  // 50ms 足够布局完成
        repeat: false
        onTriggered: _init()
    }
}
