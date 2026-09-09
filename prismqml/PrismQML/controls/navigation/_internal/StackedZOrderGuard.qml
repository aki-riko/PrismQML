// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedZOrderGuard - Shared transition z-order guard 共享切页 z 顺序守卫
QtObject {
    id: guard

    // ==================== Internal Props 内部属性 ====================
    property Item _raisedWidget: null
    property real _originalZ: 0
    property bool _captured: false

    // ==================== Public Methods 公开方法 ====================
    function capture(oldWidget, newWidget) {
        restore()
        if (!oldWidget || !newWidget) return false

        // Later dynamic-stack pages may already sit above earlier pages. Only
        // raise an incoming page when needed, then restore its caller-owned z.
        // 动态栈后创建的页面可能已盖住早期页面；仅在需要时提升进入页，并在结束后恢复调用方的 z。
        if (newWidget.z > oldWidget.z) return true

        _raisedWidget = newWidget
        _originalZ = newWidget.z
        _captured = true
        newWidget.z = oldWidget.z + 1
        return true
    }

    function restore() {
        if (!_captured) return
        if (_raisedWidget) _raisedWidget.z = _originalZ
        _raisedWidget = null
        _captured = false
    }
}
