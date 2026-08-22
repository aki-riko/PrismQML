// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ViewportContentWatcher - Track contentItem size to catch layout completion 跟踪 contentItem 尺寸以捕获布局完成
Connections {
    id: contentWatcher

    // ==================== Required Props 必需属性 ====================
    required property var host

    function onHeightChanged() { host._updateViewport() }

    objectName: "viewportContentWatcher"
    target: host._flickableAncestor ? host._flickableAncestor.contentItem : null
}
