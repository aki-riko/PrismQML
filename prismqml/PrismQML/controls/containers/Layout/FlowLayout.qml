// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts as Layouts
import "../../.."
import "FlowLayoutEngine.js" as FlowLayoutEngine
import "_internal" as LayoutInternal

// FlowLayout - Enhanced flow layout with multiple modes 增强流式布局（支持多种模式）
// Supports: default (preserve size), horizontal (equal height), vertical (equal width) 支持：默认（保持尺寸）、水平（等高）、垂直（等宽）
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Flow mode 流式模式 (Enums.flow)
    property int mode: Enums.flow.default_

    // Spacing 间距
    property int spacing: Enums.spacing.m       // Horizontal gap 水平间距
    property int rowSpacing: Enums.spacing.m    // Vertical gap 垂直间距

    // Vertical mode options 垂直模式选项
    property int columnCount: 0  // 0=auto, >0=fixed columns 列数（0为自动）

    // Aspect ratio 宽高比
    property bool preserveAspectRatio: false  // Keep aspect ratio when resizing 调整尺寸时保持宽高比

    // Content margins 内容边距
    property int leftMargin: 0
    property int topMargin: 0
    property int rightMargin: 0
    property int bottomMargin: 0

    // Content container 内容容器
    default property alias content: contentItem.data

    // ==================== Readonly State 只读状态 ====================
    readonly property int rowCount: _rowCount         // Total rows 总行数
    readonly property var rowHeights: _rowHeights     // Height of each row 每行高度
    readonly property int itemCount: contentItem.children.length  // Child count 子项数量

    // ==================== Internal Props 内部属性 ====================
    property int _rowCount: 0
    property var _rowHeights: []
    property var _originalSizes: []   // [{width, height}, ...] 原始尺寸缓存
    property bool _layoutPending: false
    property bool _initialized: false
    property bool _appendLayoutPending: false
    property bool _layoutAppendable: false
    property int _laidOutItemCount: 0
    property int _rawChildCount: 0
    property var _lastRawChild: null
    property var _pendingAppendItems: []
    property var _defaultHeightMap: []
    property real _defaultMaxHeight: 0

    // ==================== Public Methods 公开方法 ====================
    // addWidget - Add a child widget to layout 添加子组件到布局
    function addWidget(widget) {
        if (widget) {
            widget.parent = contentItem
        }
    }

    // removeWidget - Remove a widget from layout 从布局中移除组件
    function removeWidget(widget) {
        if (widget && widget.parent === contentItem) {
            widget.parent = null
        }
    }

    // setSpacing - Set layout spacing 设置布局间距
    function setSpacing(value) {
        spacing = value
        rowSpacing = value
    }

    // count - Get children count 获取子组件数量
    function count() {
        return itemCount
    }

    // setContentsMargins - Set layout margins 设置布局边距
    function setContentsMargins(left, top, right, bottom) {
        leftMargin = left
        topMargin = top
        rightMargin = right
        bottomMargin = bottom
    }

    // itemAt - Get child at index 获取指定索引的子组件
    function itemAt(index) {
        var children = _getVisibleChildren()
        if (index >= 0 && index < children.length) {
            return children[index]
        }
        return null
    }

    // indexOf - Get index of widget 获取组件索引
    function indexOf(widget) {
        var children = _getVisibleChildren()
        for (var i = 0; i < children.length; i++) {
            if (children[i] === widget) {
                return i
            }
        }
        return -1
    }

    // isEmpty - Check if layout is empty 检查布局是否为空
    function isEmpty() {
        return itemCount === 0
    }

    // clear - Remove all children 清空所有子组件
    function clear() {
        for (var i = contentItem.children.length - 1; i >= 0; i--) {
            contentItem.children[i].parent = null
        }
    }

    // insertWidget - Insert widget 插入组件
    function insertWidget(index, widget) {
        if (widget) {
            widget.parent = contentItem
        }
    }

    // ==================== Internal Methods 内部方法 ====================

    // Read engine-owned state without exposing mutable aliases 通过显式桥接读取引擎状态
    function _getEngineState(name) {
        switch (name) {
        case "layoutPending": return _layoutPending
        case "layoutAppendable": return _layoutAppendable
        case "laidOutItemCount": return _laidOutItemCount
        case "pendingAppendItems": return _pendingAppendItems
        case "defaultHeightMap": return _defaultHeightMap
        case "defaultMaxHeight": return _defaultMaxHeight
        case "rowCount": return _rowCount
        case "rowHeights": return _rowHeights
        case "originalSizes": return _originalSizes
        default: return undefined
        }
    }

    // Update engine-owned state through one validated bridge 通过统一桥接更新引擎状态
    function _setEngineState(name, value) {
        switch (name) {
        case "layoutPending": _layoutPending = value; break
        case "layoutAppendable": _layoutAppendable = value; break
        case "laidOutItemCount": _laidOutItemCount = value; break
        case "pendingAppendItems": _pendingAppendItems = value; break
        case "defaultHeightMap": _defaultHeightMap = value; break
        case "defaultMaxHeight": _defaultMaxHeight = value; break
        case "rowCount": _rowCount = value; break
        case "rowHeights": _rowHeights = value; break
        default: break
        }
    }

    function _isLayoutChild(child) {
        if (!child) return false
        if (child.toString().indexOf("QQuickRepeater") !== -1) return false
        if (typeof child.width !== "number" || typeof child.height !== "number") return false
        return child.width > 0 || child.height > 0
    }

    // Get layout children (exclude Repeater and non-visual items) 获取布局子项（排除Repeater和非可视元素）
    function _getVisibleChildren() {
        var items = []
        for (var i = 0; i < contentItem.children.length; i++) {
            var child = contentItem.children[i]
            if (_isLayoutChild(child)) items.push(child)
        }
        return items
    }

    function _trackRawChildren() {
        var rawChildren = contentItem.children
        _rawChildCount = rawChildren.length
        _lastRawChild = rawChildren.length > 0
            ? rawChildren[rawChildren.length - 1] : null
    }

    function _invalidateLayout() {
        _layoutAppendable = false
        _laidOutItemCount = 0
        _pendingAppendItems = []
        _scheduleLayout()
    }

    function _queueTailAppend() {
        var rawChildren = contentItem.children
        var rawCount = rawChildren.length
        var appendedAtEnd = rawCount === _rawChildCount + 1
            && (_rawChildCount === 0
                || rawChildren[_rawChildCount - 1] === _lastRawChild)
        var child = rawCount > 0 ? rawChildren[rawCount - 1] : null
        _trackRawChildren()
        if (!appendedAtEnd) return false
        if (!_isLayoutChild(child)) return true
        if (!_layoutAppendable || mode !== Enums.flow.default_
                || _layoutPending
                || _laidOutItemCount + _pendingAppendItems.length
                    !== _originalSizes.length) return false
        _pendingAppendItems.push(child)
        _originalSizes.push({ width: child.width, height: child.height })
        _scheduleAppendLayout()
        return true
    }

    // Cache all original sizes 缓存所有原始尺寸
    function _cacheAllOriginalSizes() {
        _originalSizes = []
        var children = _getVisibleChildren()  // Use same filter as layout 使用与布局相同的过滤
        for (var i = 0; i < children.length; i++) {
            var child = children[i]
            if (child) {
                _originalSizes.push({
                    width: child.width,
                    height: child.height
                })
            }
        }
        _trackRawChildren()
    }

    // Schedule layout update 调度布局更新
    function _scheduleLayout() {
        if (_layoutPending) return
        _layoutPending = true
        layoutTimer.restart()
    }

    function _scheduleAppendLayout() {
        if (_appendLayoutPending || _layoutPending) return
        _appendLayoutPending = true
        appendLayoutTimer.restart()
    }

    function _placeDefaultItem(item, originalSize, heightMap,
                               containerWidth, useSlidingWindow,
                               positionDeque) {
        return FlowLayoutEngine.placeDefaultItem(
            control, item, originalSize, heightMap, containerWidth,
            useSlidingWindow, positionDeque
        )
    }

    function _appendDefaultItems() {
        FlowLayoutEngine.appendDefaultItems(
            control, Enums.flow.default_, Enums.flow.sliding_window_min_items
        )
    }

    // Perform layout based on mode 根据模式执行布局
    function _performLayout() {
        FlowLayoutEngine.performLayout(
            control, Enums.flow.default_, Enums.flow.horizontal,
            Enums.flow.vertical, Enums.flow.sliding_window_min_items
        )
    }
    // Default mode layout 默认模式布局
    // Compact packing: items float up to fill gaps 紧凑填充：子项上浮填补空隙
    // Uses heightmap algorithm to find lowest available position 使用高度图算法找到最低可用位置
    function _layoutDefault(children) {
        return FlowLayoutEngine.layoutDefault(
            control, children, Enums.flow.sliding_window_min_items
        )
    }

    // Find best position for item using heightmap 使用高度图找到子项的最佳位置
    function _findBestPosition(heightMap, containerWidth, itemWidth,
                               itemHeight, useSlidingWindow, positionDeque) {
        return FlowLayoutEngine.findBestPosition(
            heightMap, containerWidth, itemWidth, itemHeight,
            useSlidingWindow, positionDeque
        )
    }

    // Select the large-layout search path 选择大布局搜索路径
    function _usesSlidingWindow(itemTotal) {
        return FlowLayoutEngine.usesSlidingWindow(
            control, itemTotal, Enums.flow.sliding_window_min_items
        )
    }
    // Horizontal mode layout 水平模式布局
    // Equal height per row 同行等高
    function _layoutHorizontal(children) {
        return FlowLayoutEngine.layoutHorizontal(
            control, children, Enums.flow.sliding_window_min_items
        )
    }

    // Calculate rows based on original sizes 根据原始尺寸计算行
    function _calculateRows(children) {
        return FlowLayoutEngine.calculateRows(control, children)
    }
    // Vertical mode layout 垂直模式布局
    // Equal width, variable height (waterfall flow) 等宽不等高（瀑布流）
    // Items are placed in the shortest column 子项放入最短的列
    function _layoutVertical(children) {
        return FlowLayoutEngine.layoutVertical(control, children)
    }

    // Calculate auto column count based on max item width 根据最大子项宽度计算自动列数
    function _calculateAutoColumnCount(children) {
        return FlowLayoutEngine.calculateAutoColumnCount(control, children)
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: 300
    implicitHeight: 0

    // Layout attached properties 布局附加属性
    // Fill parent width by default 默认填充父容器宽度
    Layouts.Layout.fillWidth: true

    // Property change handlers 属性变化处理
    onWidthChanged: {
        // Re-layout when width changes 宽度变化时重新布局
        if (width > 0) {
            // Re-cache original sizes (lazy loading may create children when width is 0) 重新缓存原始尺寸（懒加载场景下子项可能在 width 为 0 时创建）
            _cacheAllOriginalSizes()
            _layoutPending = false
            _invalidateLayout()
        }
    }
    onSpacingChanged: _invalidateLayout()
    onRowSpacingChanged: _invalidateLayout()
    onModeChanged: _invalidateLayout()
    onColumnCountChanged: _invalidateLayout()
    onPreserveAspectRatioChanged: _invalidateLayout()

    // Component initialization 组件初始化
    Component.onCompleted: {
        // Cache original sizes and perform initial layout 缓存原始尺寸并执行初始布局
        _cacheAllOriginalSizes()
        _initialized = true
        _scheduleLayout()
    }

    // ==================== Content 内容 ====================
    // Component-owned timers cancel queued work when Loader destroys the layout 组件自有定时器确保 Loader 销毁布局时取消排队任务
    LayoutInternal.FlowLayoutLayoutTimer {
        id: layoutTimer
        host: control
    }

    LayoutInternal.FlowLayoutAppendTimer {
        id: appendLayoutTimer
        host: control
    }

    Item {
        id: contentItem
        objectName: "contentItem"
        anchors.fill: parent
        anchors.leftMargin: control.leftMargin
        anchors.topMargin: control.topMargin
        anchors.rightMargin: control.rightMargin
        anchors.bottomMargin: control.bottomMargin

        onChildrenChanged: {
            if (control._initialized && !control._queueTailAppend()) {
                control._cacheAllOriginalSizes()
                control._invalidateLayout()
            }
        }
    }
}
