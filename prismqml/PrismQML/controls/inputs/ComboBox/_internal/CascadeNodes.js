// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

// CascadeNodes.js - Cascade row contract for ComboBoxCascade 级联下拉框的行数据契约
// Single owner of the cascade row shape and of the node-to-row navigation. A row is
// built by one level and consumed by the next, so both levels must agree on the
// shape; neither level may re-derive it locally.
// 级联行结构与节点到行的导航的唯一归属。行由上一层构建、由下一层消费，因此两层必须
// 对结构达成一致；任何一层都不得在本地另行推导。
// Row shape 行结构: { text, icon, enabled, path, children }
// children holds the raw child nodes, so a deeper level stays a view over the model
// and never a copy of it. children 保存原始子节点，深层级因此始终是模型的视图而非副本。

// @ts-nocheck
.pragma library

// ==================== Node Access 节点访问 ====================

// A node is a bare string or an object with text 节点是纯字符串或带 text 的对象
function label(node) {
    return typeof node === "string" ? node : (node && node.text ? node.text : "")
}

function icon(node) {
    return typeof node === "string" || !node ? "" : (node.icon || "")
}

// Nodes are enabled unless explicitly disabled 节点默认可用，除非显式禁用
function enabled(node) {
    if (typeof node === "string" || !node) return true
    return node.enabled === undefined ? true : !!node.enabled
}

// Raw child node array, or empty 原始子节点数组，无则空
function childArray(node) {
    if (typeof node === "string" || !node) return []
    var children = node.children
    if (!children || typeof children.length !== "number") return []
    return children
}

function hasChildren(node) {
    return childArray(node).length > 0
}

// ==================== Row Building 行构建 ====================

// One cascade row for a node owned by parentPath 父路径下某节点的级联行
function buildRow(node, parentPath) {
    var text = label(node)
    var parent = parentPath || []
    return {
        text: text,
        icon: icon(node),
        enabled: enabled(node),
        path: parent.concat([text]),
        children: childArray(node)
    }
}

// Cascade rows for a node array 节点数组的级联行
function buildRows(nodes) {
    return buildRowsFrom(nodes, [])
}

// Cascade rows whose paths continue an existing path 路径承接既有路径的级联行
// A deeper level must be told the path it hangs under: the committed value is the
// path from the root, so a level cannot start its own paths at the node it shows.
// 更深层级必须被告知它所挂载的路径: 提交值是根路径, 因此一层不能以自己显示的节点
// 作为路径起点。
function buildRowsFrom(nodes, basePath) {
    var rows = []
    if (!nodes || typeof nodes.length !== "number") return rows
    for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i]
        if (node === null || node === undefined) continue
        rows.push(buildRow(node, basePath))
    }
    return rows
}

// ==================== Search 搜索 ====================

// True when the node or any descendant matches 节点或任一后代命中时为真
// searchText must already be lowercased. searchText 必须已转小写。
function matches(node, searchText) {
    if (!searchText) return true
    if (label(node).toLowerCase().indexOf(searchText) >= 0) return true
    var children = childArray(node)
    for (var i = 0; i < children.length; i++) {
        if (matches(children[i], searchText)) return true
    }
    return false
}

// Keep only rows matching searchText, preserving their original path
// 仅保留命中 searchText 的行，并保留其原始路径
function filterRows(rows, searchText) {
    if (!searchText) return rows
    var result = []
    for (var i = 0; i < rows.length; i++) {
        var row = rows[i]
        if (matches({ text: row.text, children: row.children }, searchText)) {
            result.push(row)
        }
    }
    return result
}
