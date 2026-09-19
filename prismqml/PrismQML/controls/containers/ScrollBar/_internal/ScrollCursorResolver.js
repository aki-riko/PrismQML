// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// Resolve content cursors through non-interactive visual overlays.
// 穿透非交互视觉覆盖层解析内容光标。
function _candidateShape(candidate, baseZ, arrowCursor, pointingHandCursor) {
    var child = candidate.item
    if (child.enabled !== undefined && !child.enabled) {
        return child.cursorShape !== undefined ? arrowCursor : null
    }
    if (child._isHyperlink === true) return pointingHandCursor
    var nestedShape = resolve(
        child, candidate.point.x, candidate.point.y,
        baseZ, arrowCursor, pointingHandCursor
    )
    if (nestedShape !== null) return nestedShape
    if (child._cursorShapeTransparent === true) return null
    return child.cursorShape !== undefined ? child.cursorShape : null
}

function _cursorCandidates(rootItem, x, y, ignoredChild, baseZ) {
    var candidates = []
    if (!rootItem || !rootItem.children) return candidates
    for (var i = rootItem.children.length - 1; i >= 0; i--) {
        var child = rootItem.children[i]
        if (child === ignoredChild) continue
        if (!child || !child.visible || child.width === undefined
                || child.height === undefined) continue
        var point = rootItem.mapToItem(child, x, y)
        if (point.x < 0 || point.y < 0
                || point.x > child.width || point.y > child.height) continue
        var z = child.z === undefined ? baseZ : child.z
        candidates.push({ item: child, point: point, z: z, index: i })
    }
    candidates.sort(function(first, second) {
        if (first.z !== second.z) return second.z - first.z
        return second.index - first.index
    })
    return candidates
}

// Use childAt first; only inspect overlapping siblings when that path has no cursor.
// 先使用 childAt；仅当该路径没有光标时检查重叠 sibling。
function resolve(rootItem, x, y, baseZ, arrowCursor, pointingHandCursor) {
    if (!rootItem || !rootItem.children) return null
    var topChild = typeof rootItem.childAt === "function"
        ? rootItem.childAt(x, y) : null
    if (topChild && topChild !== rootItem) {
        var topPoint = rootItem.mapToItem(topChild, x, y)
        var topShape = _candidateShape(
            { item: topChild, point: topPoint },
            baseZ, arrowCursor, pointingHandCursor
        )
        if (topShape !== null) return topShape
    }
    var candidates = _cursorCandidates(rootItem, x, y, topChild, baseZ)
    for (var i = 0; i < candidates.length; i++) {
        var cursorShape = _candidateShape(
            candidates[i], baseZ, arrowCursor, pointingHandCursor
        )
        if (cursorShape !== null) return cursorShape
    }
    return null
}

function resolveFlickable(flickable, x, y, baseZ, arrowCursor, pointingHandCursor) {
    if (!flickable) return null
    var contentItem = flickable.contentItem
    if (!contentItem) {
        return resolve(flickable, x, y, baseZ, arrowCursor, pointingHandCursor)
    }
    var point = flickable.mapToItem(contentItem, x, y)
    return resolve(
        contentItem, point.x, point.y,
        baseZ, arrowCursor, pointingHandCursor
    )
}
