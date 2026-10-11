// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ItemsStackLayout - Single-axis stack layout 单轴堆叠布局
// One item per line along the scroll axis; the cross axis stretches to the viewport
// unless itemBreadth pins it.
// 沿滚动轴每行一个项目；除非 itemBreadth 固定，交叉轴拉伸到视口。
ItemsRepeaterLayout {
    id: layout

    // ==================== Public Props 公开属性 ====================
    property int orientation: Qt.Vertical
    // Main-axis extent of one item 单个项目的主轴尺寸
    property real itemExtent: Enums.controlSize.listItemHeight
    // Cross-axis extent; 0 stretches to the viewport 交叉轴尺寸; 0 表示拉伸到视口
    property real itemBreadth: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property int scrollOrientation: layout.orientation
    readonly property bool _isVertical: layout.orientation === Qt.Vertical
    readonly property real _resolvedBreadth: layout.itemBreadth > 0
        ? layout.itemBreadth
        : (layout._isVertical ? layout.viewportWidth : layout.viewportHeight)
    readonly property real _totalExtent: layout.count > 0
        ? layout.count * layout.itemExtent
            + (layout.count - 1) * layout.spacing
        : 0
    readonly property real contentWidth: layout._isVertical
        ? layout._resolvedBreadth : layout._totalExtent
    readonly property real contentHeight: layout._isVertical
        ? layout._totalExtent : layout._resolvedBreadth

    // ==================== Public Methods 公开方法 ====================
    function itemRect(index) {
        if (index < 0 || index >= layout.count) {
            return { x: 0, y: 0, width: 0, height: 0, index: index }
        }
        var offset = index * (layout.itemExtent + layout.spacing)
        if (layout._isVertical) {
            return {
                x: 0, y: offset,
                width: layout._resolvedBreadth, height: layout.itemExtent,
                index: index
            }
        }
        return {
            x: offset, y: 0,
            width: layout.itemExtent, height: layout._resolvedBreadth,
            index: index
        }
    }
}
