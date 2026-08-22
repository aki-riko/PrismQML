// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ViewportAncestorWatcher - Track the Flickable ancestor scroll state 跟踪 Flickable 祖先滚动状态
// Declarative Connections tear down with the mixin, so a destroyed consumer
// leaves no stale callback writing to a dead scope.
// 声明式 Connections 随混入组件一起销毁，消费者被销毁后不会残留回调写入已失效作用域。
Connections {
    id: ancestorWatcher

    // ==================== Required Props 必需属性 ====================
    required property var host

    function onContentYChanged() { host._updateViewport() }
    function onHeightChanged() { host._updateViewport() }

    objectName: "viewportAncestorWatcher"
    target: host._flickableAncestor
}
