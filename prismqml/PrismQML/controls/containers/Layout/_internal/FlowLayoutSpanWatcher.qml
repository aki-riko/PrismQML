// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// FlowLayoutSpanWatcher - Cross-cell span watcher 跨格变更监听
// Owns the span fingerprint of the layout children so a runtime edit of a child
// rowSpan / columnSpan re-runs the layout without an explicit invalidate call.
// 承载布局子项的跨格指纹, 使运行期修改子项 rowSpan / columnSpan 时自动重排。
Item {
    id: watcher

    // ==================== Required Props 必需属性 ====================
    required property Item host
    required property Item contentHost

    // ==================== Readonly State 只读状态 ====================
    // The binding captures every child span read 该绑定捕获每个子项的跨格读取
    readonly property int revision: {
        var total = 0
        var children = contentHost.children
        for (var index = 0; index < children.length; index++) {
            var child = children[index]
            if (typeof child.columnSpan === "number") {
                total += child.columnSpan * (index + 1)
            }
            if (typeof child.rowSpan === "number") {
                total += child.rowSpan * (index + 3)
            }
        }
        return total
    }

    // ==================== Size 尺寸 ====================
    visible: false
    onRevisionChanged: host._invalidateLayout()
}
