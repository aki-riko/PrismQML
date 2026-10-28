// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

// TreeRowStore - Incremental row bridge between a flat array and a ListModel
// 扁平数组 → ListModel 的增量行同步器
// The tree dropdowns rebuild their visible rows on every expand/collapse/search.
// Replacing a model wholesale makes the ListView recreate every delegate, so no
// add/remove/displaced transition can ever run: the rows just jump. This owner
// turns "old rows → new rows" into the smallest structural edit it can prove
// (single insertion / single deletion, the expand/collapse shape) and lets the
// view animate the rest.
// 树形下拉每次展开/折叠/搜索都会重建可见行。整表替换会让 ListView 重建全部委托,
// 增删与让位过渡就永远没有机会跑, 行是「一下子全出来」。这里把「旧行 → 新行」
// 收敛成能证明的最小结构变更(单段插入/单段删除, 正是展开/折叠的形状), 其余交给视图动画。
//
// 用法: 行字段用 key 标识身份(树的 nodeId 唯一且稳定), 其它字段按普通属性同步。
// JS 侧无状态, 调用方持有 ListModel 并传入。
.pragma library

// @ts-nocheck

// Insert one row at index 插入一行
function insertRow(model, index, row) {
    model.insert(index, row)
}

// Replace every row after a full reset 整体重建（重置换行, 不产生过渡）
function resetRows(model, rows) {
    model.clear()
    for (var i = 0; i < rows.length; i++) model.append(rows[i])
}

// Length of the shared prefix under key 公共前缀长度
function _commonPrefix(model, rows, key) {
    var limit = Math.min(model.count, rows.length)
    var index = 0
    while (index < limit && model.get(index)[key] === rows[index][key]) index++
    return index
}

// Length of the shared suffix under key, never overlapping the prefix
// 公共后缀长度（不与前缀重叠）
function _commonSuffix(model, rows, key, prefix) {
    var limit = Math.min(model.count - prefix, rows.length - prefix)
    var suffix = 0
    while (suffix < limit
            && model.get(model.count - 1 - suffix)[key]
                === rows[rows.length - 1 - suffix][key]) {
        suffix++
    }
    return suffix
}

// Reconcile model with rows. Returns "reset" | "insert" | "remove" | "update".
// 把 model 调整成 rows, 返回本次做的动作类型。
function syncRows(model, rows, key, animate) {
    if (!animate || model.count === 0) {
        resetRows(model, rows)
        return "reset"
    }
    var prefix = _commonPrefix(model, rows, key)
    var suffix = _commonSuffix(model, rows, key, prefix)
    var oldEnd = model.count - suffix
    var newEnd = rows.length - suffix

    if (oldEnd === prefix && newEnd === prefix) return "update"
    if (oldEnd === prefix) {
        for (var i = prefix; i < newEnd; i++) model.insert(i, rows[i])
        return "insert"
    }
    if (newEnd === prefix) {
        for (var j = oldEnd - 1; j >= prefix; j--) model.remove(j)
        return "remove"
    }
    resetRows(model, rows)
    return "reset"
}

// Refresh display fields on rows that kept their identity 刷新仍在位行的展示字段
function syncRowFields(model, rows, key, fields) {
    for (var i = 0; i < rows.length && i < model.count; i++) {
        var current = model.get(i)
        if (current[key] !== rows[i][key]) continue
        for (var f = 0; f < fields.length; f++) {
            var field = fields[f]
            if (current[field] !== rows[i][field]) {
                model.setProperty(i, field, rows[i][field])
            }
        }
    }
}
