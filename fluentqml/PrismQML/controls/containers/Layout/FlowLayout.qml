// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts as Layouts
import "../../.."

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

    // ==================== Read-only Props 只读属性 ====================
    readonly property int rowCount: _rowCount         // Total rows 总行数
    readonly property var rowHeights: _rowHeights     // Height of each row 每行高度
    readonly property int itemCount: contentItem.children.length  // Child count 子项数量

    // ==================== Internal State 内部状态 ====================
    property int _rowCount: 0
    property var _rowHeights: []
    property var _originalSizes: []   // [{width, height}, ...] 原始尺寸缓存
    property bool _layoutPending: false
    property bool _initialized: false

    // ==================== Size 尺寸 ====================
    implicitWidth: 300
    implicitHeight: 0
    
    // ==================== Layout attached properties 布局附加属性 ====================
    // Fill parent width by default 默认填充父容器宽度
    Layouts.Layout.fillWidth: true

    // ==================== Layout Functions 布局函数 ====================

    // Get layout children (exclude Repeater and non-visual items) 获取布局子项（排除Repeater和非可视元素）
    function _getVisibleChildren() {
        var items = []
        for (var i = 0; i < contentItem.children.length; i++) {
            var child = contentItem.children[i]
            if (!child) continue

            // Skip Repeater 跳过Repeater
            if (child.toString().indexOf("QQuickRepeater") !== -1) continue

            // Must be a visual item with valid size 必须是有效尺寸的可视元素
            if (typeof child.width !== "number" || typeof child.height !== "number") continue
            if (child.width <= 0 && child.height <= 0) continue

            items.push(child)
        }
        return items
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
    }

    // Schedule layout update 调度布局更新
    function _scheduleLayout() {
        if (_layoutPending) return
        _layoutPending = true
        Qt.callLater(_performLayout)
    }

    // Perform layout based on mode 根据模式执行布局
    function _performLayout() {
        _layoutPending = false

        // Validate mode 验证模式
        if (mode < 0 || mode > 2) {
            console.warn("FlowLayout: Invalid mode value, falling back to default")
            mode = Enums.flow.default_
            return
        }

        var children = _getVisibleChildren()

        // Skip if no items or invalid width 无子项或无效宽度时跳过
        if (children.length === 0 || control.width <= 0) {
            implicitHeight = 0
            _rowCount = 0
            _rowHeights = []
            return
        }

        // Execute layout based on mode 根据模式执行布局
        switch (mode) {
            case Enums.flow.horizontal:
                implicitHeight = _layoutHorizontal(children)
                break
            case Enums.flow.vertical:
                implicitHeight = _layoutVertical(children)
                break
            default:
                implicitHeight = _layoutDefault(children)
        }
    }
    // ==================== Default Mode Layout 默认模式布局 ====================
    // Compact packing: items float up to fill gaps 紧凑填充：子项上浮填补空隙
    // Uses heightmap algorithm to find lowest available position 使用高度图算法找到最低可用位置
    function _layoutDefault(children) {
        if (children.length === 0) return 0

        var containerWidth = Math.floor(control.width)
        // Heightmap: track occupied height at each pixel column 高度图：追踪每个像素列的已占用高度
        var heightMap = []
        for (var i = 0; i < containerWidth; i++) {
            heightMap.push(0)
        }

        var maxHeight = 0

        for (var i = 0; i < children.length; i++) {
            var item = children[i]

            // Restore original size from cache 从缓存恢复原始尺寸
            var itemWidth = _originalSizes[i] ? _originalSizes[i].width : item.width
            var itemHeight = _originalSizes[i] ? _originalSizes[i].height : item.height

            // Find best position (lowest y where item fits) 找到最佳位置（子项能放下的最低y）
            var pos = _findBestPosition(heightMap, containerWidth, itemWidth, itemHeight)

            item.x = pos.x
            item.y = pos.y
            item.width = itemWidth
            item.height = itemHeight

            // Update heightmap for occupied area 更新已占用区域的高度图
            var endX = Math.min(pos.x + itemWidth, containerWidth)
            var newHeight = pos.y + itemHeight + rowSpacing
            for (var px = pos.x; px < endX; px++) {
                heightMap[px] = newHeight
            }
            // Add spacing gap to the right 右侧添加间距
            var gapEnd = Math.min(endX + spacing, containerWidth)
            for (var gx = endX; gx < gapEnd; gx++) {
                heightMap[gx] = Math.max(heightMap[gx], newHeight)
            }

            maxHeight = Math.max(maxHeight, pos.y + itemHeight)
        }

        _rowCount = 0
        _rowHeights = []

        return maxHeight
    }

    // Find best position for item using heightmap 使用高度图找到子项的最佳位置
    function _findBestPosition(heightMap, containerWidth, itemWidth, itemHeight) {
        var bestX = 0
        var bestY = Infinity

        // Scan all possible x positions 扫描所有可能的x位置
        var maxX = containerWidth - itemWidth
        for (var x = 0; x <= maxX; x++) {
            // Find max height in the range [x, x+itemWidth) 找到范围内的最大高度
            var maxH = 0
            var endX = Math.min(x + itemWidth, containerWidth)
            for (var px = x; px < endX; px++) {
                maxH = Math.max(maxH, heightMap[px])
            }

            // If this position is lower, use it 如果这个位置更低，使用它
            if (maxH < bestY) {
                bestY = maxH
                bestX = x
            }
        }

        return { x: bestX, y: bestY }
    }
    // ==================== Horizontal Mode Layout 水平模式布局 ====================
    // Equal height per row 同行等高
    function _layoutHorizontal(children) {
        // Phase 1: Calculate rows with original sizes 第一阶段：用原始尺寸计算行
        var rows = _calculateRows(children)

        // Phase 2: Apply equal height per row 第二阶段：应用每行等高
        var y = 0
        for (var r = 0; r < rows.length; r++) {
            var row = rows[r]
            var x = 0

            for (var i = 0; i < row.items.length; i++) {
                var item = row.items[i]
                var itemIndex = row.indices[i]

                item.x = x
                item.y = y

                // Apply row height 应用行高
                if (preserveAspectRatio && _originalSizes[itemIndex]) {
                    var original = _originalSizes[itemIndex]
                    if (original.height > 0) {
                        var ratio = original.width / original.height
                        item.height = row.maxHeight
                        item.width = row.maxHeight * ratio
                    }
                } else {
                    item.height = row.maxHeight
                    // Restore original width 恢复原始宽度
                    if (_originalSizes[itemIndex]) {
                        item.width = _originalSizes[itemIndex].width
                    }
                }

                x += item.width + spacing
            }

            y += row.maxHeight + rowSpacing
        }

        _rowCount = rows.length
        _rowHeights = rows.map(r => r.maxHeight)

        return rows.length > 0 ? y - rowSpacing : 0
    }

    // Calculate rows based on original sizes 根据原始尺寸计算行
    function _calculateRows(children) {
        var rows = []
        var currentRow = { items: [], indices: [], maxHeight: 0, totalWidth: 0 }
        var x = 0

        for (var i = 0; i < children.length; i++) {
            var item = children[i]

            // Use original size for calculation 使用原始尺寸计算
            var itemWidth = _originalSizes[i] ? _originalSizes[i].width : item.width
            var itemHeight = _originalSizes[i] ? _originalSizes[i].height : item.height

            // Check if line break needed 检查是否需要换行
            if (x + itemWidth > control.width && x > 0) {
                rows.push(currentRow)
                currentRow = { items: [], indices: [], maxHeight: 0, totalWidth: 0 }
                x = 0
            }

            currentRow.items.push(item)
            currentRow.indices.push(i)
            currentRow.maxHeight = Math.max(currentRow.maxHeight, itemHeight)
            currentRow.totalWidth = x + itemWidth

            x += itemWidth + spacing
        }

        // Add last row 添加最后一行
        if (currentRow.items.length > 0) {
            rows.push(currentRow)
        }

        return rows
    }
    // ==================== Vertical Mode Layout 垂直模式布局 ====================
    // Equal width, variable height (waterfall flow) 等宽不等高（瀑布流）
    // Items are placed in the shortest column 子项放入最短的列
    function _layoutVertical(children) {
        if (children.length === 0) return 0

        // Calculate column count and item width 计算列数和子项宽度
        var cols = columnCount > 0 ? columnCount : _calculateAutoColumnCount(children)
        if (cols <= 0) cols = 1

        var itemWidth = (control.width - (cols - 1) * spacing) / cols

        // Initialize column heights 初始化各列高度
        var columnHeights = []
        for (var c = 0; c < cols; c++) {
            columnHeights.push(0)
        }

        // Place each item in the shortest column 将每个子项放入最短的列
        for (var i = 0; i < children.length; i++) {
            var item = children[i]

            // Find shortest column 找到最短的列
            var shortestCol = 0
            var minHeight = columnHeights[0]
            for (var col = 1; col < cols; col++) {
                if (columnHeights[col] < minHeight) {
                    minHeight = columnHeights[col]
                    shortestCol = col
                }
            }

            // Get original height for this item 获取子项的原始高度
            var originalHeight = _originalSizes[i] ? _originalSizes[i].height : item.height
            var originalWidth = _originalSizes[i] ? _originalSizes[i].width : item.width

            // Calculate item height 计算子项高度
            var itemHeight
            if (preserveAspectRatio && originalWidth > 0) {
                // Scale height proportionally 按比例缩放高度
                var ratio = originalHeight / originalWidth
                itemHeight = itemWidth * ratio
            } else {
                // Keep original height 保持原始高度
                itemHeight = originalHeight
            }

            // Position and size item 定位和设置子项尺寸
            item.x = shortestCol * (itemWidth + spacing)
            item.y = columnHeights[shortestCol]
            item.width = itemWidth
            item.height = itemHeight  // Apply calculated height 应用计算的高度

            // Update column height 更新列高度
            columnHeights[shortestCol] += itemHeight + rowSpacing
        }

        // Calculate max height 计算最大高度
        var maxHeight = 0
        for (var h = 0; h < columnHeights.length; h++) {
            maxHeight = Math.max(maxHeight, columnHeights[h])
        }

        _rowCount = cols
        _rowHeights = columnHeights

        return maxHeight > 0 ? maxHeight - rowSpacing : 0
    }

    // Calculate auto column count based on max item width 根据最大子项宽度计算自动列数
    function _calculateAutoColumnCount(children) {
        var maxWidth = 0
        for (var i = 0; i < _originalSizes.length; i++) {
            if (_originalSizes[i]) {
                maxWidth = Math.max(maxWidth, _originalSizes[i].width)
            }
        }
        if (maxWidth <= 0) maxWidth = 100
        return Math.max(1, Math.floor((control.width + spacing) / (maxWidth + spacing)))
    }
    // ==================== Qt-Style Layout Methods Qt风格布局方法 ====================
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

    // ==================== Content Item 内容容器 ====================
    Item {
        id: contentItem
        objectName: "contentItem"
        anchors.fill: parent
        anchors.leftMargin: control.leftMargin
        anchors.topMargin: control.topMargin
        anchors.rightMargin: control.rightMargin
        anchors.bottomMargin: control.bottomMargin

        onChildrenChanged: {
            if (control._initialized) {
                control._cacheAllOriginalSizes()
                control._scheduleLayout()
            }
        }
    }

    // ==================== Property Change Handlers 属性变化处理 ====================
    onWidthChanged: {
        // Re-layout when width changes 宽度变化时重新布局
        if (width > 0) {
            // Re-cache original sizes (lazy loading may create children when width is 0) 重新缓存原始尺寸（懒加载场景下子项可能在 width 为 0 时创建）
            _cacheAllOriginalSizes()
            _layoutPending = false
            _scheduleLayout()
        }
    }
    onSpacingChanged: _scheduleLayout()
    onRowSpacingChanged: _scheduleLayout()
    onModeChanged: _scheduleLayout()
    onColumnCountChanged: _scheduleLayout()
    onPreserveAspectRatioChanged: _scheduleLayout()

    // ==================== Component Initialization 组件初始化 ====================
    Component.onCompleted: {
        // Cache original sizes and perform initial layout 缓存原始尺寸并执行初始布局
        _cacheAllOriginalSizes()
        _initialized = true
        _scheduleLayout()
    }
}
