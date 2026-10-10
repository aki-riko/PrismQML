// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../prismqml/PrismQML/controls/data/List"

// ItemsRepeaterStaggerLayout - Test-only staggered layout 仅测试用的错位布局
// Proves the repeater honours a third-party layout: odd rows are pushed sideways and
// the geometry is not producible by the built-in stack or uniform grid layouts.
// 证明重复器支持第三方布局: 奇数行横向错位, 内置堆叠与等宽网格都产生不了该几何。
ItemsRepeaterLayout {
    id: layout

    // ==================== Public Props 公开属性 ====================
    property real itemHeight: 40
    property real stagger: 20

    // ==================== Readonly State 只读状态 ====================
    readonly property real contentWidth: layout.viewportWidth
    readonly property real contentHeight: layout.count > 0
        ? layout.count * layout.itemHeight : 0

    // ==================== Public Methods 公开方法 ====================
    function itemRect(index) {
        if (index < 0 || index >= layout.count) {
            return { x: 0, y: 0, width: 0, height: 0, index: index }
        }
        var staggered = index % 2 === 1
        return {
            x: staggered ? layout.stagger : 0,
            y: index * layout.itemHeight,
            width: Math.max(0, layout.viewportWidth - (staggered ? layout.stagger : 0)),
            height: layout.itemHeight,
            index: index
        }
    }
}
