// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../../.."
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ScrollAreaDefault - Default scroll area implementation 默认滚动区域实现
// For arbitrary content, no virtualization 用于任意内容，无虚拟化
// Supports horizontal/vertical/both scroll directions 支持水平/垂直/双向滚动
// Refactored to use SmoothScrollHelper 重构为使用SmoothScrollHelper
Item {
    id: control
    
    // ==================== Props from parent 继承自父组件的属性 ====================
    property bool showScrollBar: true
    property int scrollBarWidth: Enums.controlSize.scrollBarWidth
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    property int orientation: Qt.Horizontal | Qt.Vertical  // Scroll direction 滚动方向
    property int padding: Enums.spacing.xl  // Content padding 内容内边距
    
    // ==================== Content 内容 ====================
    default property alias content: contentHolder.data
    
    // ==================== Expose props 暴露属性 ====================
    property alias contentY: flickable.contentY
    property alias contentX: flickable.contentX
    property alias contentHeight: flickable.contentHeight
    property alias contentWidth: flickable.contentWidth
    property alias flickableItem: flickable
    
    // ==================== Internal 内部 ====================
    readonly property bool _canScrollV: orientation & Qt.Vertical
    readonly property bool _canScrollH: orientation & Qt.Horizontal

    // Track if scrollbar should show (breaks binding loop) 跟踪滚动条是否显示
    property bool _needsVScrollBar: false
    property bool _needsHScrollBar: false
    onHeightChanged: Qt.callLater(_updateScrollBar)
    onWidthChanged: Qt.callLater(_updateScrollBar)
    function _updateScrollBar() {
        _needsVScrollBar = _canScrollV && flickable.contentHeight > flickable.height
        _needsHScrollBar = _canScrollH && flickable.contentWidth > flickable.width
    }

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

    // ==================== Nested Scroll Dispatcher 嵌套滚动调度 ====================
    // 嵌套 ScrollArea(及兼容 ListWidget/TableWidget)的滚轮事件由外层统一调度：
    //   1. 命中点向下递归找可滚子组件（识别 smoothScrollBy 函数 / listView 鸭子类型）
    //   2. 子组件未到边界 → 调它的 smoothScrollBy(delta)
    //   3. 子组件到边界 → 由当前层处理（自己滚 / 再往父级透传）
    // 不依赖 event.accepted=false 冒泡（QML wheel 不是 composed event，冒泡不可靠），
    // 改为外层主动调度子组件方法，更稳定。
    function _findScrollableChild(rootItem, mouseX, mouseY, delta) {
        if (!rootItem || !rootItem.children) return null
        for (var i = rootItem.children.length - 1; i >= 0; i--) {
            var child = rootItem.children[i]
            if (!child || !child.visible) continue
            var pt = rootItem.mapToItem(child, mouseX, mouseY)
            if (pt.x < 0 || pt.y < 0 || pt.x > child.width || pt.y > child.height) continue
            // 优先递归命中更深层
            var deeper = _findScrollableChild(child, pt.x, pt.y, delta)
            if (deeper) return deeper
            // 嵌套 ScrollArea：暴露了 smoothScrollBy/contentY/contentHeight
            if (typeof child.smoothScrollBy === "function"
                && child.contentHeight !== undefined && child.height !== undefined
                && child.contentHeight > child.height) {
                var atEnd = child.contentY >= (child.contentHeight - child.height) - 1
                var atBegin = child.contentY <= 1
                var towardEnd = delta > 0
                var towardBegin = delta < 0
                var atBoundary = (atEnd && towardEnd) || (atBegin && towardBegin)
                return { item: child, atBoundary: atBoundary }
            }
            // 兼容 a890fbd0 旧场景：ListWidget/TableWidget 通过 listView 暴露
            if (child.listView && child.listView.contentHeight !== undefined
                && child.listView.contentHeight > child.listView.height) {
                var lvAtEnd = child.listView.contentY >= (child.listView.contentHeight - child.listView.height) - 1
                var lvAtBegin = child.listView.contentY <= 1
                var lvBoundary = (lvAtEnd && delta > 0) || (lvAtBegin && delta < 0)
                return { item: child, atBoundary: lvBoundary }
            }
        }
        return null
    }

    // ==================== Flickable 可滚动区域 ====================
    Flickable {
        id: flickable
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.rightMargin: showScrollBar && control._needsVScrollBar ? scrollBarWidth + Enums.spacing.xs : 0
        anchors.bottomMargin: showScrollBar && control._needsHScrollBar ? scrollBarWidth + Enums.spacing.xs : 0

        // childrenRect 在子项使用 anchors.fill / Layout.fillHeight 时会坍缩到 0;
        // 由 contentHolder 自己用一次性 implicit 兜底, 不在 Flickable 这条绑定里跑 for 循环
        // (老实现每次任何子孙 implicit 抖动都让全树 for 重跑, 是 default 模式滚动卡顿的回归源).
        contentWidth: contentHolder.implicitWidth + control.padding * 2
        contentHeight: contentHolder.implicitHeight + control.padding * 2
        clip: true
        interactive: false

        onContentHeightChanged: Qt.callLater(control._updateScrollBar)
        onContentWidthChanged: Qt.callLater(control._updateScrollBar)

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
    
    // ==================== Smooth Scroll Helpers 平滑滚动助手 ====================
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

    // ==================== Vertical Scrollbar 垂直滚动条 ====================
    ScrollBar {
        id: vBar
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.bottomMargin: control._needsHScrollBar ? scrollBarWidth + Enums.spacing.xs : Enums.spacing.xxs
        anchors.margins: Enums.spacing.xxs
        
        target: flickable
        scrollHelper: vScrollHelper
        orientation: Qt.Vertical
        barWidth: scrollBarWidth
        visible: showScrollBar && control._needsVScrollBar
    }
    
    // ==================== Horizontal Scrollbar 水平滚动条 ====================
    ScrollBar {
        id: hBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: Enums.spacing.xxs
        anchors.rightMargin: control._needsVScrollBar ? scrollBarWidth + Enums.spacing.xs : Enums.spacing.xxs
        anchors.bottomMargin: Enums.spacing.xxs
        
        target: flickable
        scrollHelper: hScrollHelper
        orientation: Qt.Horizontal
        barWidth: scrollBarWidth
        visible: showScrollBar && control._needsHScrollBar
    }

    // ==================== Mouse Wheel 鼠标滚轮 ====================
    MouseArea {
        anchors.fill: flickable
        propagateComposedEvents: true
        hoverEnabled: false  // Prevent hover interference with child components 防止干扰子组件hover状态
        z: Enums.zIndex.background
        onWheel: (event) => {
            var horizontal = (event.modifiers & Qt.ShiftModifier) && control._canScrollH
            var useV = !horizontal && control._canScrollV
            var useH = horizontal || (!control._canScrollV && control._canScrollH)
            var delta = -event.angleDelta.y / 120 * (useV ? vScrollHelper.step : hScrollHelper.step)

            // Step 1: 命中点向下递归找可滚子组件，未到边界则调它的 smoothScrollBy
            var hit = control._findScrollableChild(flickable, event.x, event.y, delta)
            if (hit && !hit.atBoundary) {
                if (useH && typeof hit.item.smoothScrollByX === "function") {
                    hit.item.smoothScrollByX(delta)
                } else if (typeof hit.item.smoothScrollBy === "function") {
                    hit.item.smoothScrollBy(delta)
                } else if (hit.item.listView && hit.item.listView.flick) {
                    hit.item.listView.flick(0, -event.angleDelta.y * 4)
                }
                event.accepted = true
                return
            }

            // Step 2: 自己处理。已到边界且仍向边界外滚 → accepted=false 透传给父级
            if (useH) {
                var hPos = hScrollHelper.targetPos
                if ((hPos >= hScrollHelper.maxScroll - 1 && delta > 0)
                    || (hPos <= 1 && delta < 0)) {
                    if (!control.smoothScroll || !hScrollHelper.bounceEnabled) {
                        event.accepted = false
                        return
                    }
                }
                hScrollHelper.scrollBy(delta)
                event.accepted = true
                return
            }
            if (useV) {
                var vPos = vScrollHelper.targetPos
                if ((vPos >= vScrollHelper.maxScroll - 1 && delta > 0)
                    || (vPos <= 1 && delta < 0)) {
                    if (!control.smoothScroll || !vScrollHelper.bounceEnabled) {
                        event.accepted = false
                        return
                    }
                }
                vScrollHelper.scrollBy(delta)
                event.accepted = true
                return
            }
            // 无可滚动方向：透传
            event.accepted = false
        }
        onPressed: (event) => event.accepted = false
        onReleased: (event) => event.accepted = false
        onClicked: (event) => event.accepted = false
    }
}
