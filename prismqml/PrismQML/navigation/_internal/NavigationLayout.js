// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// NavigationLayout - Layout helpers for sparse navigation models 导航稀疏模型布局辅助

function isVisible(item) {
    return !item || item.visible !== false
}

function visibleCount(items) {
    if (!items || typeof items.length !== "number") return 0

    var count = 0
    for (var index = 0; index < items.length; index++) {
        if (isVisible(items[index])) count += 1
    }
    return count
}

function contentHeight(items, itemHeight, itemSpacing) {
    var count = visibleCount(items)
    return count > 0 ? count * itemHeight + (count - 1) * itemSpacing : 0
}

function itemY(items, index, itemHeight, itemSpacing) {
    if (!items || typeof items.length !== "number") return 0

    var y = 0
    var end = Math.min(Math.max(0, index), items.length)
    for (var current = 0; current < end; current++) {
        if (isVisible(items[current])) y += itemHeight + itemSpacing
    }
    return y
}
