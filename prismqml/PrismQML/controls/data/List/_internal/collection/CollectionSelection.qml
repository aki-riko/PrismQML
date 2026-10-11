// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../../.."

// CollectionSelection - Selection state machine for collection views 集合视图选择状态机
// Shared by ItemsView and ScrollAreaGrid so both expose identical selection
// semantics. Modes come from Enums.scroll.selection_*.
// 由 ItemsView 与 ScrollAreaGrid 共享, 使两者暴露完全一致的选择语义。
// 模式取自 Enums.scroll.selection_*。
QtObject {
    id: selection

    // ==================== Public Props 公开属性 ====================
    property int mode: Enums.scroll.selection_none
    property int itemCount: 0

    // ==================== Internal Props 内部属性 ====================
    // Selected membership map: index -> true 选中成员表: 索引 -> true
    property var _selected: ({})
    // Range anchor for Extended mode Extended 模式的区间锚点
    property int _anchorIndex: -1
    // Most recently touched index 最近触及的索引
    property int _leadIndex: -1
    property int _revision: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property var selectedIndexes: {
        selection._revision
        return selection._buildIndexes()
    }
    readonly property int selectedCount: {
        selection._revision
        return Object.keys(selection._selected).length
    }
    readonly property int currentIndex: selection._leadIndex
    readonly property int anchorIndex: selection._anchorIndex

    // ==================== Signals 信号 ====================
    signal selectionChanged()

    // ==================== Public Methods 公开方法 ====================
    function isSelected(index) {
        return selection._selected[index] === true
    }

    // Apply one user click with the keyboard modifiers that came with it.
    // 按用户点击及其键盘修饰键应用选择。
    function handleClick(index, modifiers) {
        if (index < 0 || index >= selection.itemCount) return
        if (selection.mode === Enums.scroll.selection_none) return
        selection._leadIndex = index
        if (selection.mode === Enums.scroll.selection_single) {
            selection._replaceWith(index)
            selection._anchorIndex = index
        } else if (selection.mode === Enums.scroll.selection_multiple) {
            selection._setMembership(index, !selection.isSelected(index))
            selection._anchorIndex = index
        } else {
            var control = (modifiers & Qt.ControlModifier) !== 0
            var shift = (modifiers & Qt.ShiftModifier) !== 0
            if (shift && selection._anchorIndex >= 0) {
                selection._replaceWithRange(selection._anchorIndex, index)
            } else if (control) {
                selection._setMembership(index, !selection.isSelected(index))
                selection._anchorIndex = index
            } else {
                selection._replaceWith(index)
                selection._anchorIndex = index
            }
        }
        selection._commit()
    }

    // Programmatic selection of one index. 以编程方式选择单个索引。
    function selectIndex(index, selected) {
        if (index < 0 || index >= selection.itemCount) return
        if (selection.mode === Enums.scroll.selection_none) return
        selection._leadIndex = index
        selection._anchorIndex = index
        if (selection.mode === Enums.scroll.selection_single) {
            if (selected) selection._replaceWith(index)
            else selection._selected = ({})
        } else {
            selection._setMembership(index, selected)
        }
        selection._commit()
    }

    function clear() {
        selection._selected = ({})
        selection._commit()
    }

    function selectAll() {
        if (selection.mode === Enums.scroll.selection_none || selection.itemCount <= 0) return
        selection._selected = ({})
        if (selection.mode === Enums.scroll.selection_single) {
            selection._selected[0] = true
            selection._leadIndex = 0
            selection._anchorIndex = 0
        } else {
            for (var index = 0; index < selection.itemCount; ++index) {
                selection._selected[index] = true
            }
            selection._leadIndex = selection.itemCount - 1
            selection._anchorIndex = 0
        }
        selection._commit()
    }

    // Switching mode must never leave stale membership behind.
    // 切换模式不得留下过期的选中成员。
    function setMode(nextMode) {
        selection.mode = nextMode
    }

    // Drop members that fell outside a shrunken model. 丢弃收缩后越界的选中成员。
    function pruneToCount(count) {
        var keys = Object.keys(selection._selected)
        var changed = false
        for (var cursor = 0; cursor < keys.length; ++cursor) {
            var index = parseInt(keys[cursor], 10)
            if (index >= count) {
                delete selection._selected[index]
                changed = true
            }
        }
        if (selection._leadIndex >= count) {
            selection._leadIndex = -1
            changed = true
        }
        if (selection._anchorIndex >= count) selection._anchorIndex = -1
        if (changed) selection._commit()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _commit() {
        selection._revision = selection._revision + 1
        selection.selectionChanged()
    }

    function _buildIndexes() {
        var keys = Object.keys(selection._selected)
        var indexes = []
        for (var cursor = 0; cursor < keys.length; ++cursor) {
            indexes.push(parseInt(keys[cursor], 10))
        }
        indexes.sort(function ascending(left, right) { return left - right })
        return indexes
    }

    function _setMembership(index, selected) {
        if (selected) selection._selected[index] = true
        else delete selection._selected[index]
    }

    function _replaceWith(index) {
        selection._selected = ({})
        selection._selected[index] = true
    }

    function _replaceWithRange(from, to) {
        selection._selected = ({})
        var first = Math.min(from, to)
        var last = Math.max(from, to)
        for (var index = first; index <= last; ++index) {
            selection._selected[index] = true
        }
    }

    function _normalizeMode() {
        if (selection.mode === Enums.scroll.selection_none) {
            selection._selected = ({})
            selection._anchorIndex = -1
            selection._leadIndex = -1
            selection._commit()
            return
        }
        if (selection.mode === Enums.scroll.selection_single) {
            var keys = Object.keys(selection._selected)
            if (keys.length > 1) {
                var keep = selection._leadIndex >= 0
                    ? selection._leadIndex : parseInt(keys[0], 10)
                selection._replaceWith(keep)
                selection._commit()
            }
        }
    }

    onModeChanged: selection._normalizeMode()
    onItemCountChanged: selection.pruneToCount(selection.itemCount)
}
