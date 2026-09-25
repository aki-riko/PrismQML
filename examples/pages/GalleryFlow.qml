// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML as Fluent

// GalleryFlow - Responsive example layout 响应式示例布局
// Fills the available card width and wraps examples onto a new row.
// 填满卡片可用宽度，并在空间不足时自动换行。
Flow {
    id: control

    // ==================== Size 尺寸 ====================
    width: parent && parent.width > 0 ? parent.width : implicitWidth
    height: childrenRect.height
    spacing: Fluent.Enums.spacing.l
    flow: Flow.LeftToRight
}
