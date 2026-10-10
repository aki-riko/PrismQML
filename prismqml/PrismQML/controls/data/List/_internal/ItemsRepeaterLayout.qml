// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ItemsRepeaterLayout - Pluggable layout contract for ItemsRepeater 重复器可插拔布局契约
// A layout decides where every item sits and which indices the viewport touches.
// 布局决定每个项目的位置以及视口触及的索引范围。
// Contract 契约:
//   viewportWidth / viewportHeight — written by the repeater 由重复器写入
//   count                          — written by the repeater 由重复器写入
//   scrollOrientation              — Qt.Vertical or Qt.Horizontal 滚动轴
//   contentWidth / contentHeight   — scrollable content extent 可滚动内容范围
//   itemRect(index)                — item geometry in content coordinates 内容坐标中的项目几何
//   indexRangeFor(offset, extent)  — inclusive visible index range 可见索引闭区间
//   indexAt(x, y)                  — hit test, -1 when nothing is hit 命中测试, 未命中为 -1
// Derive from this type and override itemRect() plus contentWidth/contentHeight. The
// generic range and hit-test helpers stay correct while itemRect() is monotonic along
// the scroll axis.
// 派生本类型并覆写 itemRect() 与 contentWidth/contentHeight。只要 itemRect() 沿滚动轴单调,
// 通用范围与命中测试辅助保持正确。
QtObject {
    id: layout

    // ==================== Public Props 公开属性 ====================
    property real viewportWidth: 0
    property real viewportHeight: 0
    property int count: 0
    property real spacing: Enums.spacing.none

    // ==================== Readonly State 只读状态 ====================
    readonly property int scrollOrientation: Qt.Vertical
    readonly property real contentWidth: 0
    readonly property real contentHeight: 0

    // ==================== Public Methods 公开方法 ====================
    // Abstract geometry of one item; derived layouts override it.
    // 单个项目的抽象几何；派生布局覆写它。
    function itemRect(index) {
        return { x: 0, y: 0, width: 0, height: 0, index: index }
    }

    // Inclusive range of indices intersecting the viewport window.
    // 与视口窗口相交的索引闭区间。
    function indexRangeFor(offset, extent) {
        if (count <= 0) return { first: 0, last: -1 }
        return { first: _firstVisible(offset), last: _lastVisible(offset + extent) }
    }

    // Hit test in content coordinates. 内容坐标中的命中测试。
    function indexAt(x, y) {
        if (count <= 0) return -1
        var probe = scrollOrientation === Qt.Vertical ? _firstVisible(y) : _firstVisible(x)
        if (probe >= count) probe = count - 1
        var last = Math.min(count - 1, probe + 1)
        for (var index = Math.max(0, probe - 1); index <= last; ++index) {
            var rect = itemRect(index)
            if (rect && x >= rect.x && x < rect.x + rect.width
                    && y >= rect.y && y < rect.y + rect.height) {
                return index
            }
        }
        return -1
    }

    // ==================== Internal Methods 内部方法 ====================
    // Leading edge of an item on the scroll axis. 项目在滚动轴上的前缘。
    function _mainAxisStart(index) {
        var rect = itemRect(index)
        if (!rect) return 0
        return scrollOrientation === Qt.Vertical ? rect.y : rect.x
    }

    // Trailing edge of an item on the scroll axis. 项目在滚动轴上的后缘。
    function _mainAxisEnd(index) {
        var rect = itemRect(index)
        if (!rect) return 0
        return scrollOrientation === Qt.Vertical
            ? rect.y + rect.height : rect.x + rect.width
    }

    // Smallest index whose trailing edge passes the offset. 后缘越过偏移量的最小索引。
    function _firstVisible(offset) {
        var low = 0
        var high = count - 1
        var result = count
        while (low <= high) {
            var middle = Math.floor((low + high) / 2)
            if (_mainAxisEnd(middle) > offset) {
                result = middle
                high = middle - 1
            } else {
                low = middle + 1
            }
        }
        return result
    }

    // Largest index whose leading edge precedes the limit. 前缘早于上限的最大索引。
    function _lastVisible(limit) {
        var low = 0
        var high = count - 1
        var result = -1
        while (low <= high) {
            var middle = Math.floor((low + high) / 2)
            if (_mainAxisStart(middle) < limit) {
                result = middle
                low = middle + 1
            } else {
                high = middle - 1
            }
        }
        return result
    }
}

