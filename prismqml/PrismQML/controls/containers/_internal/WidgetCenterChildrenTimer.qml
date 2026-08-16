// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// WidgetCenterChildrenTimer - Center Widget content after child changes 子项变化后居中 Widget 内容
Timer {
    id: centerChildrenTimer

    // ==================== Required Props 必需属性 ====================
    required property Item host

    objectName: "widgetCenterChildrenTimer"
    interval: Enums.duration.tick
    repeat: false
    onTriggered: {
        for (var i = 0; i < host.children.length; i++) {
            var child = host.children[i]
            if (host._isCenterableChild(child)) {
                // Center through anchors for broad child compatibility 使用锚点居中以兼容不同子项。
                child.anchors.centerIn = host
                break
            }
        }
    }
}
