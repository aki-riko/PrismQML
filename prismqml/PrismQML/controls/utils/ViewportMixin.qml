// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "_internal" as UtilsInternal

// ViewportMixin - Viewport visibility detection mixin 可视区域检测混入组件
// Used to optimize scroll performance, pauses animations when not visible 用于优化滚动性能，不可见时暂停动画

// Usage: ViewportMixin { id: viewport; target: control }
// Then use: viewport.isInViewport to control animations
QtObject {
    id: mixin
    
    // ==================== Required Props 必需属性 ====================
    required property Item target  // 要检测的目标组件

    // ==================== Public Props 公开属性 ====================
    property bool isInViewport: true  // 默认可见
    property bool ready: false  // 初始化完成标志

    // ==================== Internal Props 内部属性 ====================
    property var _flickableAncestor: null

    property Timer initTimer: UtilsInternal.ViewportInitTimer {
        host: mixin
    }

    property QtObject targetWatcher: UtilsInternal.ViewportTargetWatcher {
        host: mixin
    }

    property QtObject ancestorWatcher: UtilsInternal.ViewportAncestorWatcher {
        host: mixin
    }

    property QtObject contentWatcher: UtilsInternal.ViewportContentWatcher {
        host: mixin
    }

    // ==================== Internal Methods 内部方法 ====================
    // Find Flickable ancestor upwards 向上查找 Flickable 祖先
    function _findFlickable() {
        if (!target) return null
        var p = target.parent
        while (p) {
            if (p instanceof Flickable) return p
            p = p.parent
        }
        return null
    }

    // Calculate if target is in visible viewport 计算是否在可视区域
    function _updateViewport() {
        try {
            // An invisible target never animates, with or without a Flickable.
            // 不可见目标一律不动画，无论有没有 Flickable。
            if (!target) {
                isInViewport = false
                return
            }
            // No Flickable found, fall back to plain visibility 找不到 Flickable 时退回可见性
            if (!_flickableAncestor || !target.visible) {
                isInViewport = target.visible
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
    
    // Resolve the ancestor and recompute 解析祖先并重算
    // Idempotent: runs once synchronously and again after the layout settles.
    // Signal wiring is declarative (see the watchers below), so re-running never
    // stacks duplicate connections and destruction leaves no stale callback.
    // 幂等：同步跑一次、布局稳定后再跑一次。信号连接由下方声明式 watcher 负责，
    // 因此重跑不会叠加连接，销毁后也不残留回调。
    function _init() {
        _flickableAncestor = _findFlickable()
        _updateViewport()
        ready = true  // 标记初始化完成
    }

    // Initialize synchronously so consumers never observe a stale default, then
    // re-run once the layout has settled to pick up final geometry.
    // 先同步初始化，避免消费者读到过期默认值；再在布局稳定后重跑一次取最终几何。
    Component.onCompleted: {
        _init()
        initTimer.start()
    }
}
