// RelativePanelEngine - Relative relation solver 相对关系求解器
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

// Axis directives 轴向关系键
// x axis 横轴: leftOf / rightOf / alignLeftWith / alignRightWith /
//   alignHorizontalCenterWith / alignLeftWithPanel / alignRightWithPanel /
//   alignHorizontalCenterWithPanel
// y axis 纵轴: above / below / alignTopWith / alignBottomWith /
//   alignVerticalCenterWith / alignTopWithPanel / alignBottomWithPanel /
//   alignVerticalCenterWithPanel

function hasXDirective(relation) {
    return relation.leftOf !== undefined
        || relation.rightOf !== undefined
        || relation.alignLeftWith !== undefined
        || relation.alignRightWith !== undefined
        || relation.alignHorizontalCenterWith !== undefined
        || relation.alignLeftWithPanel === true
        || relation.alignRightWithPanel === true
        || relation.alignHorizontalCenterWithPanel === true
}

function hasYDirective(relation) {
    return relation.above !== undefined
        || relation.below !== undefined
        || relation.alignTopWith !== undefined
        || relation.alignBottomWith !== undefined
        || relation.alignVerticalCenterWith !== undefined
        || relation.alignTopWithPanel === true
        || relation.alignBottomWithPanel === true
        || relation.alignVerticalCenterWithPanel === true
}

function findRelation(relations, item) {
    if (!relations || !relations.length) return null
    for (var index = 0; index < relations.length; index++) {
        var relation = relations[index]
        if (relation && relation.item === item) return relation
    }
    return null
}

function referenceFrame(frames, item) {
    if (item === undefined || item === null) return null
    for (var index = 0; index < frames.length; index++) {
        if (frames[index].item === item) return frames[index]
    }
    return null
}

function resolveX(frame, relation, frames, panelWidth) {
    var reference
    if (relation.leftOf !== undefined) {
        reference = referenceFrame(frames, relation.leftOf)
        if (reference && reference.x !== null) return reference.x - frame.width
    }
    if (relation.rightOf !== undefined) {
        reference = referenceFrame(frames, relation.rightOf)
        if (reference && reference.x !== null) {
            return reference.x + reference.width
        }
    }
    if (relation.alignLeftWith !== undefined) {
        reference = referenceFrame(frames, relation.alignLeftWith)
        if (reference && reference.x !== null) return reference.x
    }
    if (relation.alignRightWith !== undefined) {
        reference = referenceFrame(frames, relation.alignRightWith)
        if (reference && reference.x !== null) {
            return reference.x + reference.width - frame.width
        }
    }
    if (relation.alignHorizontalCenterWith !== undefined) {
        reference = referenceFrame(frames, relation.alignHorizontalCenterWith)
        if (reference && reference.x !== null) {
            return reference.x + (reference.width - frame.width) / 2
        }
    }
    if (relation.alignLeftWithPanel === true) return 0
    if (relation.alignRightWithPanel === true) return panelWidth - frame.width
    if (relation.alignHorizontalCenterWithPanel === true) {
        return (panelWidth - frame.width) / 2
    }
    return null
}

function resolveY(frame, relation, frames, panelHeight) {
    var reference
    if (relation.above !== undefined) {
        reference = referenceFrame(frames, relation.above)
        if (reference && reference.y !== null) return reference.y - frame.height
    }
    if (relation.below !== undefined) {
        reference = referenceFrame(frames, relation.below)
        if (reference && reference.y !== null) {
            return reference.y + reference.height
        }
    }
    if (relation.alignTopWith !== undefined) {
        reference = referenceFrame(frames, relation.alignTopWith)
        if (reference && reference.y !== null) return reference.y
    }
    if (relation.alignBottomWith !== undefined) {
        reference = referenceFrame(frames, relation.alignBottomWith)
        if (reference && reference.y !== null) {
            return reference.y + reference.height - frame.height
        }
    }
    if (relation.alignVerticalCenterWith !== undefined) {
        reference = referenceFrame(frames, relation.alignVerticalCenterWith)
        if (reference && reference.y !== null) {
            return reference.y + (reference.height - frame.height) / 2
        }
    }
    if (relation.alignTopWithPanel === true) return 0
    if (relation.alignBottomWithPanel === true) return panelHeight - frame.height
    if (relation.alignVerticalCenterWithPanel === true) {
        return (panelHeight - frame.height) / 2
    }
    return null
}

// resolve - Solve every child frame 求解每个子项的几何
// items: [{ item, width, height }] natural sizes 自然尺寸
// returns { geometry: [{ item, x, y, width, height }], unresolved: int }
function resolve(items, relations, panelWidth, panelHeight) {
    var frames = []
    for (var index = 0; index < items.length; index++) {
        var entry = items[index]
        var relation = findRelation(relations, entry.item)
        var width = entry.width
        var height = entry.height
        var x = null
        var y = null
        // Panel edge pairs stretch the child across the whole panel
        // 面板双侧对齐让子项撑满整个面板
        if (relation && relation.alignLeftWithPanel === true
                && relation.alignRightWithPanel === true) {
            x = 0
            width = panelWidth
        }
        if (relation && relation.alignTopWithPanel === true
                && relation.alignBottomWithPanel === true) {
            y = 0
            height = panelHeight
        }
        frames.push({
            item: entry.item,
            relation: relation,
            x: x,
            y: y,
            width: width,
            height: height
        })
    }

    // Iterate until every reachable reference resolves 迭代到所有可达引用求解完成
    for (var pass = 0; pass < frames.length + 1; pass++) {
        for (var frameIndex = 0; frameIndex < frames.length; frameIndex++) {
            var frame = frames[frameIndex]
            if (!frame.relation) continue
            if (frame.x === null) {
                var resolvedX = resolveX(frame, frame.relation, frames, panelWidth)
                if (resolvedX !== null) frame.x = resolvedX
            }
            if (frame.y === null) {
                var resolvedY = resolveY(frame, frame.relation, frames, panelHeight)
                if (resolvedY !== null) frame.y = resolvedY
            }
        }
    }

    var geometry = []
    var unresolved = 0
    for (var output = 0; output < frames.length; output++) {
        var current = frames[output]
        if (current.relation) {
            if (hasXDirective(current.relation) && current.x === null) unresolved++
            else if (hasYDirective(current.relation) && current.y === null) unresolved++
        }
        geometry.push({
            item: current.item,
            x: current.x === null ? 0 : current.x,
            y: current.y === null ? 0 : current.y,
            width: current.width,
            height: current.height
        })
    }
    return { geometry: geometry, unresolved: unresolved }
}
