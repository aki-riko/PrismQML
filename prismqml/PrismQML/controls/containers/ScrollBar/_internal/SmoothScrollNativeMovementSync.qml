// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// SmoothScrollNativeMovementSync - Rebase after native flicking 原生拖拽结束后重置平滑滚动基准
Connections {
    id: sync

    // ==================== Required Props 必需属性 ====================
    required property var scrollHelper

    function onMovementEnded() {
        scrollHelper.syncPosition()
    }

    target: scrollHelper ? scrollHelper.target : null
}
