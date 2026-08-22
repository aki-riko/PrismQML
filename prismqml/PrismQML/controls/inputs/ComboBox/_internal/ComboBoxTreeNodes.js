// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

// ComboBoxTreeNodes.js - Shared tree traversal for tree ComboBoxes 树形下拉框共享遍历
// Single owner of the node-id scheme, the search-match rules and the walk order.
// ComboBoxTree and ComboBoxMultiTree differ only in how they emit a visible row,
// so the walk takes an emit callback and stays free of selection concerns.
// 节点 id 规则、搜索匹配规则与遍历顺序的唯一归属。ComboBoxTree 与
// ComboBoxMultiTree 只在"如何产出一行"上不同，因此遍历接受 emit 回调，
// 自身不涉及任何选中语义。

// @ts-nocheck
.pragma library

// ==================== Node Basics 节点基础 ====================

// Stable id for a node at index under parentId 父 id 下指定下标节点的稳定 id
function nodeId(parentId, index) {
    return parentId + "_" + index
}

// A node may be a bare string or an object with text 节点可以是纯字符串或带 text 的对象
function nodeLabel(node) {
    return typeof node === "string" ? node : (node.text || "")
}

function hasChildren(node) {
    return !!(node && node.children && node.children.length > 0)
}

// ==================== Expansion 展开 ====================

// Collect every expandable node id into result 收集所有可展开节点 id 到 result
function collectExpandable(nodes, parentId, result) {
    if (!nodes) return
    for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i]
        if (!node) continue
        var id = nodeId(parentId, i)
        if (hasChildren(node)) {
            result[id] = true
            collectExpandable(node.children, id, result)
        }
    }
}

// Every expandable node id, expanded 所有可展开节点 id 的展开态
function expandAll(nodes) {
    var expanded = ({})
    collectExpandable(nodes, "root", expanded)
    return expanded
}

// Flip one node, returning a new map so QML sees a fresh value
// 翻转单个节点并返回新对象，便于 QML 感知变化
function toggleExpanded(expandedNodes, id) {
    var next = Object.assign({}, expandedNodes)
    next[id] = !next[id]
    return next
}

// ==================== Search 搜索 ====================

// True when any descendant label contains searchText 任一后代标签命中 searchText 时为真
// searchText must already be lowercased. searchText 必须已转小写。
function hasMatchingDescendants(children, searchText) {
    if (!children) return false
    for (var i = 0; i < children.length; i++) {
        var child = children[i]
        if (!child) continue
        if (nodeLabel(child).toLowerCase().indexOf(searchText) >= 0) return true
        if (child.children && hasMatchingDescendants(child.children, searchText)) {
            return true
        }
    }
    return false
}

// ==================== Traversal 遍历 ====================

// Walk the visible tree and hand each row to emit 遍历可见树并把每行交给 emit
// ctx: { expandedNodes, searchText }  searchText already lowercased 已转小写
// emit receives { node, text, depth, nodeId, path, hasChildren, expanded }
// so a caller can layer its own per-row state on top. 调用方可在此之上叠加自有行状态。
function flatten(nodes, ctx, emit) {
    _walk(nodes, [], 0, "root", ctx, emit)
}

function _walk(nodes, parentPath, depth, parentId, ctx, emit) {
    if (!nodes) return
    for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i]
        if (!node) continue
        var label = nodeLabel(node)
        var id = nodeId(parentId, i)
        var path = parentPath.concat([label])
        var childful = hasChildren(node)
        var expanded = !!ctx.expandedNodes[id]
        var matches = !ctx.searchText
                || label.toLowerCase().indexOf(ctx.searchText) >= 0

        var matchingChildren = false
        if (!matches && childful) {
            matchingChildren = hasMatchingDescendants(node.children, ctx.searchText)
        }

        // With no search active every node is visible 未搜索时所有节点可见
        if (matches || matchingChildren || !ctx.searchText) {
            emit({
                node: node,
                text: label,
                depth: depth,
                nodeId: id,
                path: path,
                hasChildren: childful,
                expanded: expanded
            })
        }

        if (childful && expanded) {
            _walk(node.children, path, depth + 1, id, ctx, emit)
        }
    }
}
