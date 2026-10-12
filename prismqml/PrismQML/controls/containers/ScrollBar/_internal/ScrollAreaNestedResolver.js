// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// Find the deepest visible scrollable child that owns the requested axis.
// 查找最深层且支持目标滚动轴的可见子视口。
function findScrollableChild(control, rootItem, mouseX, mouseY, delta, horizontal) {
    return _findScrollableChildOnAxis(
        control, rootItem, mouseX, mouseY, delta, horizontal
    )
}

function _findScrollableChildOnAxis(control, rootItem, mouseX, mouseY, delta, horizontal) {
    if (!rootItem || !rootItem.children) return null
    for (var i = rootItem.children.length - 1; i >= 0; i--) {
        var child = rootItem.children[i]
        if (!child || !child.visible) continue
        // A nested surface that does not own this axis must not be descended into.
        // 不支持当前轴的嵌套滚动面不得继续下钻。
        if (!control._supportsScrollAxis(child, horizontal)) continue
        var point = rootItem.mapToItem(child, mouseX, mouseY)
        if (point.x < 0 || point.y < 0
                || point.x > child.width || point.y > child.height) continue
        var deeper = _findScrollableChildOnAxis(
            control, child, point.x, point.y, delta, horizontal
        )
        if (deeper) {
            if (!deeper.scrollHelper) {
                deeper.scrollHelper = control._findScrollHelper(
                    child, deeper.viewport, horizontal
                )
            }
            return deeper
        }
        var viewport = control._scrollViewport(
            child, horizontal, point.x, point.y
        )
        if (!viewport || !control._hasScrollOverflow(viewport, horizontal)) continue
        var scrollHelper = control._findScrollHelper(child, viewport, horizontal)
        if (!scrollHelper) {
            scrollHelper = control._findScrollHelper(rootItem, viewport, horizontal)
        }
        var hasAxisScrollMethod = horizontal
            ? typeof child.smoothScrollByX === "function"
            : typeof child.smoothScrollBy === "function"
        if (!hasAxisScrollMethod && !scrollHelper
                && !control._hasScrollOverflow(viewport, horizontal)) continue
        return {
            item: child,
            viewport: viewport,
            scrollHelper: scrollHelper,
            horizontal: horizontal,
            atBoundary: control._isAtScrollBoundary(viewport, delta, horizontal)
        }
    }
    return null
}
