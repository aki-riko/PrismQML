// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ViewportTargetWatcher - Track target visibility and geometry 跟踪目标可见性与几何变化
// The mixin is a QtObject, so it cannot use onVisibleChanged itself.
// 混入组件是 QtObject，无法自己用 onVisibleChanged，因此由本组件代为监听。
Connections {
    id: watcher

    // ==================== Required Props 必需属性 ====================
    required property var host

    // Visibility always matters, with or without a Flickable.
    // 可见性无论有没有 Flickable 都要重算。
    function onVisibleChanged() { host._updateViewport() }

    // Geometry only matters while a Flickable ancestor exists.
    // 几何变化只在存在 Flickable 祖先时才影响结果。
    function onYChanged() { if (host._flickableAncestor) host._updateViewport() }
    function onHeightChanged() { if (host._flickableAncestor) host._updateViewport() }

    objectName: "viewportTargetWatcher"
    target: host.target
    enabled: host.ready
}
