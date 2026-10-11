// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ItemsUniformGridLayout - Wrapping uniform grid layout 等宽换行网格布局
// Fits as many columns as minItemWidth allows, then stretches every cell to the
// remaining viewport width.
// 在 minItemWidth 允许的范围内排满列数, 再把每个单元格拉伸到剩余视口宽度。
ItemsRepeaterLayout {
    id: layout

    // ==================== Public Props 公开属性 ====================
    // Smallest accepted column width; the real cell width is derived from it
    // 允许的最小列宽; 真实单元格宽度由它推导
    property real minItemWidth: Enums.controlSize.listDefaultWidth
    property real itemHeight: Enums.controlSize.listItemHeight

    // ==================== Readonly State 只读状态 ====================
    readonly property real _stride: layout.minItemWidth + layout.spacing
    readonly property int itemsPerRow: layout._stride > 0 && layout.viewportWidth > 0
        ? Math.max(1, Math.floor((layout.viewportWidth + layout.spacing) / layout._stride))
        : 1
    readonly property real cellWidth: layout.itemsPerRow > 0
        ? Math.max(0, (layout.viewportWidth
            - (layout.itemsPerRow - 1) * layout.spacing) / layout.itemsPerRow)
        : 0
    readonly property int rowCount: layout.count > 0
        ? Math.ceil(layout.count / layout.itemsPerRow)
        : 0
    readonly property real contentWidth: layout.viewportWidth
    readonly property real contentHeight: layout.rowCount > 0
        ? layout.rowCount * layout.itemHeight
            + (layout.rowCount - 1) * layout.spacing
        : 0

    // ==================== Public Methods 公开方法 ====================
    function itemRect(index) {
        if (index < 0 || index >= layout.count) {
            return { x: 0, y: 0, width: 0, height: 0, index: index }
        }
        var row = Math.floor(index / layout.itemsPerRow)
        var column = index % layout.itemsPerRow
        return {
            x: column * (layout.cellWidth + layout.spacing),
            y: row * (layout.itemHeight + layout.spacing),
            width: layout.cellWidth,
            height: layout.itemHeight,
            index: index
        }
    }
}
