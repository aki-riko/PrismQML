// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// SmoothScrollAnchorKeeper - Keeps visible content still across content re-measurement
// SmoothScrollAnchorKeeper - 内容重估时让可见内容停在原地
//
// A virtual item view estimates the height of the delegates it has not created yet.
// While scrolling those estimates are refined (Qt averages the delegates it has already
// measured), so the content range swings by hundreds of pixels and every item above the
// viewport is re-positioned. The view rewrites only `contentHeight`, never `contentY`,
// so the visible content slides relative to the viewport: a real chat list measured a
// 96px whole-screen jump mid-scroll and 176px for a single recycled bubble.
//
// 虚拟项视图会为尚未孵化的委托估算高度。滚动中这些估算被不断修正（Qt 用已测量委托的
// 平均值），内容总范围会摆动几百像素，视口上方每条都被重新定位；而视图只改写
// `contentHeight`、从不改写 `contentY`，于是可见内容相对视口整体滑动——真实聊天列表
// 实测滚动途中整屏跳 96px，单条被复用的气泡跳 176px。
//
// The baseline is the anchor row's **content coordinate**, not its offset from the
// viewport edge. A content-coordinate baseline is untouched by ordinary scrolling, so
// the per-frame scroll publishes cannot absorb the re-measurement into the baseline —
// measuring against the viewport-relative offset did exactly that and made the
// compensation a no-op.
//
// 基准取锚点行的**内容坐标**，而不是它距视口边缘的偏移。内容坐标不受普通滚动影响，
// 因此逐帧的滚动发布不会把重排量吸收进基准——用视口相对偏移做基准时正是这样失效的。
QtObject {
    id: keeper

    // ==================== Required Props 必需属性 ====================
    required property var scrollHelper

    // ==================== Public Props 公开属性 ====================
    // Enabled by the helper. Axes that are not item-indexed (plain Flickable, TextEdit,
    // TableView without itemAtIndex) are skipped automatically.
    // 由 helper 打开；轴向不是条目索引的视图（普通 Flickable / TextEdit）自动跳过。
    property bool enabled: true

    // ==================== Internal Props 内部属性 ====================
    property int _anchorRow: -1
    property real _anchorContentY: -1
    property bool _applying: false
    // Total distance this keeper has put back, for diagnostics and gates.
    // 本组件累计补回的位移，供诊断与门禁读取。
    property real compensatedDistance: 0

    readonly property bool _vertical: scrollHelper ? scrollHelper._isVertical : true
    readonly property var _view: scrollHelper ? scrollHelper.target : null
    readonly property real _epsilon: 0.5

    // ==================== Public Methods 公开方法 ====================
    // Re-pick the anchor row when it left the viewport. Re-picking on every axis move
    // would absorb a re-measurement into the baseline, so it is deliberately limited to
    // the case where the tracked row can no longer serve as the anchor.
    // 锚点行离开视口时才重挑。每次轴移动都重挑会把重排量吸收进基准，因此刻意只在
    // 被跟踪的行不再能当锚点时重挑。
    function syncAnchor() {
        if (!_anchorable()) return
        if (_anchorRow >= 0 && _anchorInView()) return
        _pickAnchor()
    }

    // Content range changed: shift the axis by however much the anchor row moved in
    // content coordinates. Only changes above the anchor move it, so content growing
    // below the viewport is left alone.
    // 内容范围变化：锚点行在内容坐标里挪了多少，就把轴补回多少。只有锚点上方的变化
    // 才会移动它，因此视口下方增删内容不受影响。
    function compensate() {
        if (!_anchorable()) return
        // No usable anchor yet (the axis has not moved since the delegates appeared):
        // pick one now so the next re-measurement is covered. The first re-measurement
        // after a pick cannot be compensated — there is nothing to compare against.
        // 还没有可用锚点（委托出现后轴一直没动过）：先挑一个，让下一次重测能被覆盖。
        // 挑完当次的重测无法补偿——没有可比对的基准。
        if (_anchorRow < 0 || _anchorContentY < 0) {
            _pickAnchor()
            return
        }
        var helper = scrollHelper
        // An intentional excursion (boundary bounce) must not be anchored away.
        // 有意越界（边界回弹）不得被锚定抵消。
        if (_vertical) {
            if (helper._isOutwardBounceV || helper._isOvershotV) return
        } else if (helper._isOutwardBounceH || helper._isOvershotH) return
        var item = _view.itemAtIndex(_anchorRow)
        if (!item) {
            _pickAnchor()
            return
        }
        var delta = item.y - _anchorContentY
        if (Math.abs(delta) < _epsilon) return
        _applying = true
        if (_vertical) _applyVertical(delta)
        else _applyHorizontal(delta)
        _applying = false
        _anchorContentY = item.y
    }

    // ==================== Internal Methods 内部方法 ====================
    function _anchorable() {
        var view = _view
        return enabled && !_applying && view !== null && view !== undefined
            && typeof view.indexAt === "function"
            && typeof view.itemAtIndex === "function"
    }

    function _anchorInView() {
        var item = _view.itemAtIndex(_anchorRow)
        if (!item) return false
        var position = _vertical ? _view.contentY : _view.contentX
        var extent = _vertical ? _view.height : _view.width
        var size = _vertical ? item.height : item.width
        var start = _vertical ? item.y : item.x
        return start + size > position && start < position + extent
    }

    function _pickAnchor() {
        var view = _view
        var position = _vertical ? view.contentY : view.contentX
        var row = view.indexAt(1, position + 1)
        var item = row >= 0 ? view.itemAtIndex(row) : null
        if (!item) {
            _anchorRow = -1
            _anchorContentY = -1
            return
        }
        _anchorRow = row
        _anchorContentY = _vertical ? item.y : item.x
    }

    function _applyVertical(delta) {
        var helper = scrollHelper
        var view = _view
        var currentSmooth = helper._smoothY
        var nextSmooth = helper._clamp(currentSmooth + delta, helper._minY, helper._maxY)
        var applied = nextSmooth - currentSmooth
        compensatedDistance += applied
        helper._targetY = helper._clamp(helper._targetY + applied, helper._minY, helper._maxY)
        // The running animation recomputes its live value from its own endpoints every
        // frame, so the endpoints must move with the axis or the next frame writes the
        // un-anchored position straight back.
        // 进行中的动画每帧都按自己的端点重算实时值；端点必须跟着平移，否则下一帧会把
        // 未锚定的位置原样写回来。
        helper.verticalFrameDriver.rebaseBy(applied)
        helper._discardingStaleFrameV = true
        helper._lastPublishedY = nextSmooth
        helper._smoothY = nextSmooth
        if (view.contentY !== nextSmooth) view.contentY = nextSmooth
        helper._discardingStaleFrameV = false
    }

    function _applyHorizontal(delta) {
        var helper = scrollHelper
        var view = _view
        var currentSmooth = helper._smoothX
        var nextSmooth = helper._clamp(currentSmooth + delta, helper._minX, helper._maxX)
        var applied = nextSmooth - currentSmooth
        compensatedDistance += applied
        helper._targetX = helper._clamp(helper._targetX + applied, helper._minX, helper._maxX)
        helper.horizontalFrameDriver.rebaseBy(applied)
        helper._discardingStaleFrameH = true
        helper._lastPublishedX = nextSmooth
        helper._smoothX = nextSmooth
        if (view.contentX !== nextSmooth) view.contentX = nextSmooth
        helper._discardingStaleFrameH = false
    }

    objectName: "smoothScrollAnchorKeeper"

    // A re-measuring view rewrites its content range in the same turn as it moves the
    // items, so the anchor must be compared in that same turn; deferring to the next
    // event-loop turn would let the shifted frame render.
    // 重测视图在同一轮内改写内容范围并移动条目，锚点必须在同一轮内比较；推到下一轮
    // 会让跳变的那一帧上屏。
    property Connections viewSync: Connections {
        target: keeper._view

        function onContentYChanged() {
            if (keeper._vertical) keeper.syncAnchor()
        }

        function onContentXChanged() {
            if (!keeper._vertical) keeper.syncAnchor()
        }

        function onContentHeightChanged() {
            if (keeper._vertical) keeper.compensate()
        }

        function onContentWidthChanged() {
            if (!keeper._vertical) keeper.compensate()
        }
    }
}
