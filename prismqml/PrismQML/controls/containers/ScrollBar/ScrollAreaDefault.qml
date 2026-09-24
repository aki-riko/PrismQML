// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import QtQuick  // After library import: unprefixed native types stay unshadowed 置于库import后:去前缀后保原生类型不被库覆盖
import "_internal/ScrollCursorResolver.js" as ScrollCursorResolver

// ScrollAreaDefault - Default scroll area implementation 默认滚动区域实现
// For arbitrary content, no virtualization 用于任意内容，无虚拟化
// Supports horizontal/vertical/both scroll directions 支持水平/垂直/双向滚动
// Refactored to use SmoothScrollHelper 重构为使用SmoothScrollHelper
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property bool showScrollBar: true
    property int scrollBarWidth: Enums.controlSize.scrollBarWidth
    property bool smoothScroll: true
    // Enable native touch/mouse drag scrolling 启用原生触摸/鼠标拖拽滚动
    property bool dragScrollEnabled: true
    // Optional resolver for content-specific pointer cursors 可选的内容专用指针光标解析器
    property var cursorShapeResolver: null
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    property int orientation: Qt.Horizontal | Qt.Vertical  // Scroll direction 滚动方向
    property int padding: Enums.spacing.xl  // Content padding 内容内边距
    property Item wheelHost: control
    
    default property alias content: contentHolder.data

    // Exposed aliases 暴露别名
    property alias contentY: flickable.contentY
    property alias contentX: flickable.contentX
    property alias contentHeight: flickable.contentHeight
    property alias contentWidth: flickable.contentWidth
    property alias flickableItem: flickable
    
    // ==================== Readonly State 只读状态 ====================
    readonly property bool _canScrollV: orientation & Qt.Vertical
    readonly property bool _canScrollH: orientation & Qt.Horizontal
    readonly property alias _needsVScrollBar: scrollViewportState.needsVertical
    readonly property alias _needsHScrollBar: scrollViewportState.needsHorizontal
    readonly property alias _reserveVScrollBarGutter:
        scrollViewportState.reserveVerticalGutter
    readonly property alias _reserveHScrollBarGutter:
        scrollViewportState.reserveHorizontalGutter
    readonly property real _scrollBarGutter:
        Math.max(0, scrollBarWidth) + Enums.spacing.xs
    // The hit-test cursor is a pointer-only affordance, so it stays off on touch
    // 命中测试光标只对指针有意义, 触摸端关闭该效果
    readonly property int _activeCursorShape: !Touch.isTouch && cursorHandler.hovered
        ? _cursorShapeAt(cursorHandler.point.position.x, cursorHandler.point.position.y)
        : Qt.ArrowCursor

    // ==================== Public Methods 公开方法 ====================
    function smoothScrollTo(targetY) {
        if (_canScrollV) vScrollHelper.scrollTo(targetY)
    }

    function smoothScrollToX(targetX) {
        if (_canScrollH) hScrollHelper.scrollTo(targetX)
    }

    function smoothScrollBy(delta) {
        if (_canScrollV) vScrollHelper.scrollBy(delta)
    }

    function smoothScrollByX(delta) {
        if (_canScrollH) hScrollHelper.scrollBy(delta)
    }

    // ==================== Internal Methods 内部方法 ====================
    function _updateScrollBar() {
        if (scrollViewportState) scrollViewportState.invalidate()
    }

    function _supportsScrollAxis(item, horizontal) {
        if (!item) return false
        var axis = horizontal ? Qt.Horizontal : Qt.Vertical
        if (typeof item.orientation === "number"
                && (item.flickableItem !== undefined
                    || item._canScrollH !== undefined
                    || item._canScrollV !== undefined)) {
            return (item.orientation & axis) !== 0
        }
        return true
    }

    function _scrollViewport(item, horizontal, mouseX, mouseY) {
        if (!item || !_supportsScrollAxis(item, horizontal)) return null
        var direct = item.flickableItem || item.listView || item.gridView || null
        if (direct && _hasScrollOverflow(direct, horizontal)) return direct
        var positionName = horizontal ? "contentX" : "contentY"
        var extentName = horizontal ? "contentWidth" : "contentHeight"
        if (item[positionName] !== undefined && item[extentName] !== undefined
                && _hasScrollOverflow(item, horizontal)) {
            return item
        }
        if (!item.children) return null
        for (var i = item.children.length - 1; i >= 0; i--) {
            var child = item.children[i]
            if (!child || !child.visible) continue
            var point = item.mapToItem(child, mouseX, mouseY)
            if (point.x < 0 || point.y < 0
                    || point.x > child.width || point.y > child.height) continue
            var viewport = _scrollViewport(
                child, horizontal, point.x, point.y
            )
            if (viewport) {
                return viewport
            }
        }
        return null
    }

    function _hasScrollOverflow(viewport, horizontal) {
        if (!viewport) return false
        return horizontal
            ? viewport.contentWidth > viewport.width
            : viewport.contentHeight > viewport.height
    }

    function _findScrollHelper(rootItem, viewport, horizontal) {
        if (!rootItem) return null
        var axis = horizontal ? Qt.Horizontal : Qt.Vertical
        if (typeof rootItem.scrollBy === "function"
                && rootItem.orientation === axis && rootItem.target === viewport) {
            return rootItem
        }
        if (typeof rootItem.children !== "object") return null
        for (var i = rootItem.children.length - 1; i >= 0; i--) {
            var nested = _findScrollHelper(
                rootItem.children[i], viewport, horizontal
            )
            if (nested) return nested
        }
        return null
    }

    function _cursorShapeAt(x, y) {
        if (typeof cursorShapeResolver === "function") return cursorShapeResolver(x, y)
        var cursorShape = ScrollCursorResolver.resolveFlickable(
            flickable, x, y, Enums.zIndex.base,
            Qt.ArrowCursor, Qt.PointingHandCursor
        )
        return cursorShape === null ? Qt.ArrowCursor : cursorShape
    }

    function _isAtScrollBoundary(viewport, delta, horizontal) {
        var origin = horizontal ? viewport.originX : viewport.originY
        var position = horizontal ? viewport.contentX : viewport.contentY
        var contentSize = horizontal ? viewport.contentWidth : viewport.contentHeight
        var viewportSize = horizontal ? viewport.width : viewport.height
        var end = origin + Math.max(0, contentSize - viewportSize)
        return (position >= end - 1 && delta > 0)
            || (position <= origin + 1 && delta < 0)
    }

    function _wheelDeltaForAxis(wheelY, wheelX, horizontal) {
        return horizontal ? (wheelX !== 0 ? wheelX : wheelY) : wheelY
    }

    function _wheelAxis(wheelY, wheelX, modifiers) {
        var horizontal = (modifiers & Qt.ShiftModifier) && _canScrollH
        var useV = !horizontal && _canScrollV
        var useH = horizontal || (!_canScrollV && _canScrollH && wheelX !== 0)
        var rawDelta = useH && wheelX !== 0 ? wheelX : wheelY
        return {
            horizontal: useH,
            enabled: useV || useH,
            delta: -rawDelta / 120
                * (useH ? hScrollHelper.step : vScrollHelper.step)
        }
    }

    function _scrollNestedHit(hit, wheelY, wheelX) {
        var horizontal = hit.horizontal === true
        var rawDelta = horizontal && wheelX !== 0 ? wheelX : wheelY
        var step = horizontal ? hScrollHelper.step : vScrollHelper.step
        var delta = -rawDelta / 120 * step
        if (hit.scrollHelper) {
            hit.scrollHelper.scrollBy(delta)
            return true
        }
        if (horizontal && typeof hit.item.smoothScrollByX === "function") {
            hit.item.smoothScrollByX(delta)
            return true
        }
        if (!horizontal && typeof hit.item.smoothScrollBy === "function") {
            hit.item.smoothScrollBy(delta)
            return true
        }
        if (!hit.viewport || typeof hit.viewport.flick !== "function") return false
        if (horizontal) hit.viewport.flick(-rawDelta * 4, 0)
        else hit.viewport.flick(0, -rawDelta * 4)
        return true
    }

    function _scrollOwnAxis(axis) {
        var helper = axis.horizontal ? hScrollHelper : vScrollHelper
        if (!_hasScrollOverflow(flickable, axis.horizontal)) return false
        var position = helper.targetPos
        var atOutwardBoundary = (position >= helper.maxScroll - 1 && axis.delta > 0)
            || (position <= helper.minScroll + 1 && axis.delta < 0)
        if (atOutwardBoundary && !helper.bounceEnabled) return false
        helper.scrollBy(axis.delta)
        return true
    }

    function _dispatchWheelToAncestor(wheelY, wheelX, modifiers, mouseX, mouseY) {
        var ancestor = wheelHost.parent
        while (ancestor) {
            if (typeof ancestor._handleWheel === "function"
                    && ancestor.flickableItem
                    && ancestor.flickableItem !== flickable) {
                var point = flickable.mapToItem(
                    ancestor.flickableItem, mouseX, mouseY
                )
                if (ancestor._handleWheel(
                        wheelY, wheelX, modifiers, point.x, point.y)) return true
            }
            ancestor = ancestor.parent
        }
        return false
    }

    function _handleWheel(wheelY, wheelX, modifiers, mouseX, mouseY) {
        var axis = _wheelAxis(wheelY, wheelX, modifiers)
        if (!axis.enabled) {
            return _dispatchWheelToAncestor(
                wheelY, wheelX, modifiers, mouseX, mouseY
            )
        }
        var hit = _findScrollableChild(
            flickable, mouseX, mouseY, axis.delta, axis.horizontal
        )
        if (hit && !hit.atBoundary && _scrollNestedHit(hit, wheelY, wheelX)) {
            return true
        }
        if (_scrollOwnAxis(axis)) return true
        return _dispatchWheelToAncestor(
            wheelY, wheelX, modifiers, mouseX, mouseY
        )
    }

    // Nested scroll dispatcher 嵌套滚动调度
    // 嵌套 ScrollArea(及兼容 ListWidget/TableWidget)的滚轮事件由外层统一调度：
    //   1. 命中点向下递归找可滚子组件（识别 smoothScrollBy 函数 / listView 鸭子类型）
    //   2. 子组件未到边界 → 调它的 smoothScrollBy(delta)
    //   3. 子组件到边界 → 由当前层处理（自己滚 / 再往父级透传）
    // 不依赖 event.accepted=false 冒泡（QML wheel 不是 composed event，冒泡不可靠），
    // 改为外层主动调度子组件方法，更稳定。
    function _findScrollableChildOnAxis(rootItem, mouseX, mouseY, delta, horizontal) {
        if (!rootItem || !rootItem.children) return null
        for (var i = rootItem.children.length - 1; i >= 0; i--) {
            var child = rootItem.children[i]
            if (!child || !child.visible) continue
            // A nested scroll surface that does not own this axis must not be
            // descended into: its inner Flickable carries no orientation property,
            // so a foreign-axis overflow would otherwise be adopted as a target.
            // 声明不支持当前轴的嵌套滚动面不得继续下钻: 其内部 Flickable 没有
            // orientation 属性, 否则另一轴的溢出会被误当成滚动目标。
            if (!_supportsScrollAxis(child, horizontal)) continue
            var pt = rootItem.mapToItem(child, mouseX, mouseY)
            if (pt.x < 0 || pt.y < 0 || pt.x > child.width || pt.y > child.height) continue
            // Prefer recursing into a deeper hit 优先递归命中更深层
            var deeper = _findScrollableChildOnAxis(
                child, pt.x, pt.y, delta, horizontal
            )
            if (deeper) {
                if (!deeper.scrollHelper) {
                    deeper.scrollHelper = _findScrollHelper(
                        child, deeper.viewport, horizontal
                    )
                }
                return deeper
            }
            // Nested ScrollArea: compute bounds from the real Flickable/ListView/GridView viewport 嵌套 ScrollArea：始终以真实 Flickable/ListView/GridView 视口计算边界。
            var viewport = _scrollViewport(
                child, horizontal, pt.x, pt.y
            )
            if (!viewport || !_hasScrollOverflow(viewport, horizontal)) continue
            var scrollHelper = _findScrollHelper(child, viewport, horizontal)
            if (!scrollHelper) {
                scrollHelper = _findScrollHelper(rootItem, viewport, horizontal)
            }
            var scrollOwner = child
            var hasAxisScrollMethod = horizontal
                ? typeof scrollOwner.smoothScrollByX === "function"
                : typeof scrollOwner.smoothScrollBy === "function"
            if (!hasAxisScrollMethod && !scrollHelper
                    && !_hasScrollOverflow(viewport, horizontal)) continue
            return {
                item: scrollOwner,
                viewport: viewport,
                scrollHelper: scrollHelper,
                horizontal: horizontal,
                atBoundary: _isAtScrollBoundary(viewport, delta, horizontal)
            }
        }
        return null
    }

    // Only dispatch descendants that support the requested axis.
    // 只把事件派发给支持当前滚轮轴的后代，不把纵向滚轮改成横向滚动。
    function _findScrollableChild(rootItem, mouseX, mouseY, delta, horizontal) {
        return _findScrollableChildOnAxis(
            rootItem, mouseX, mouseY, delta, horizontal
        )
    }

    onHeightChanged: _updateScrollBar()
    onWidthChanged: _updateScrollBar()
    onScrollBarWidthChanged: _updateScrollBar()

    // ==================== Content 内容 ====================
    // Flickable scroll area 可滚动区域
    Flickable {
        id: flickable
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.rightMargin: showScrollBar && control._reserveVScrollBarGutter
            ? Math.min(control._scrollBarGutter, Math.max(0, parent.width)) : 0
        anchors.bottomMargin: showScrollBar && control._reserveHScrollBarGutter
            ? Math.min(control._scrollBarGutter, Math.max(0, parent.height)) : 0

        // childrenRect 在子项使用 anchors.fill / Layout.fillHeight 时会坍缩到 0;
        // 由 contentHolder 自己用一次性 implicit 兜底, 不在 Flickable 这条绑定里跑 for 循环
        // (老实现每次任何子孙 implicit 抖动都让全树 for 重跑, 是 default 模式滚动卡顿的回归源).
        contentWidth: contentHolder.implicitWidth + control.padding * 2
        contentHeight: contentHolder.implicitHeight + control.padding * 2
        clip: true
        interactive: control.dragScrollEnabled
        Item {
            id: contentHolder
            objectName: "contentHolder"
            x: control.padding
            y: control.padding
            width: flickable.width > 0 ? flickable.width - control.padding * 2 : control.width - control.padding * 2

            // implicitWidth/Height: 直接用 Qt 引擎维护的 childrenRect (一级 native 计算).
            // 不再 for 循环遍 children[i].implicit —— 那会让所有子孙 implicit 抖动
            // 都触发整段 binding 重跑, 是滚动条出现/消失瞬间引发响应式风暴的根源.
            // 约定: 调用方 ScrollArea 子项必须是 Column/Row/Flow 这类自身能正确报告
            // childrenRect 的容器 (gallery 13 个页面已全量验证为 Column/Flow/Row);
            // 不要把 anchors.fill 子项直接塞 ScrollArea, 它会让 childrenRect 坍缩到 0.
            implicitWidth: childrenRect.width
            implicitHeight: childrenRect.height
        }
    }

    ScrollViewportState {
        id: scrollViewportState
        target: flickable
        scrollBarsEnabled: control.showScrollBar
        verticalEnabled: control._canScrollV
        horizontalEnabled: control._canScrollH
    }
    
    // Smooth scroll helpers 平滑滚动助手
    SmoothScrollHelper {
        id: vScrollHelper
        target: flickable
        orientation: Qt.Vertical
        enabled: control.smoothScroll && control._canScrollV
        duration: control.scrollDuration
        step: control.scrollStep
        easing: control.scrollEasing
        bounceEnabled: true
    }
    
    SmoothScrollHelper {
        id: hScrollHelper
        target: flickable
        orientation: Qt.Horizontal
        enabled: control.smoothScroll && control._canScrollH
        duration: control.scrollDuration
        step: control.scrollStep
        easing: control.scrollEasing
        bounceEnabled: true
    }

    // Vertical scrollbar 垂直滚动条
    ScrollBar {
        id: vBar
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.bottomMargin: control._reserveHScrollBarGutter
            ? Math.min(control._scrollBarGutter, Math.max(0, parent.height))
            : Enums.spacing.xxs
        anchors.margins: Enums.spacing.xxs
        
        target: flickable
        scrollHelper: vScrollHelper
        orientation: Qt.Vertical
        barWidth: Math.max(0, scrollBarWidth)
        visible: showScrollBar && control._needsVScrollBar
    }
    
    // Horizontal scrollbar 水平滚动条
    ScrollBar {
        id: hBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: Enums.spacing.xxs
        anchors.rightMargin: control._reserveVScrollBarGutter
            ? Math.min(control._scrollBarGutter, Math.max(0, parent.width))
            : Enums.spacing.xxs
        anchors.bottomMargin: Enums.spacing.xxs
        
        target: flickable
        scrollHelper: hScrollHelper
        orientation: Qt.Horizontal
        barWidth: Math.max(0, scrollBarWidth)
        visible: showScrollBar && control._needsHScrollBar
    }

    // Mouse wheel 鼠标滚轮
    // Keep wheel ownership in Qt's pointer-handler chain so deeper controls can
    // consume their own wheel input before this scroll surface. 使用 Qt 指针处理器
    // 链维护滚轮所有权，让更深层控件先消费自己的滚轮事件。
    WheelHandler {
        parent: flickable
        blocking: true
        enabled: control.smoothScroll
        onWheel: (event) => {
            var wheelY = WheelEventUtils.verticalDelta(event)
            var wheelX = WheelEventUtils.horizontalDelta(event)
            event.accepted = control._handleWheel(
                wheelY, wheelX, event.modifiers, event.x, event.y
            )
        }
    }

    HoverHandler {
        id: cursorHandler

        parent: flickable
        cursorShape: control._activeCursorShape
    }
}
