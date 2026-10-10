// FlowLayoutEngine - Flow layout algorithms 流式布局算法引擎
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function getState(layout, name) {
    return layout._getEngineState(name)
}

function setState(layout, name, value) {
    layout._setEngineState(name, value)
}

// Span contract 跨格约定:
// A layout child may declare optional rowSpan / columnSpan integers (>= 1) on
// itself; PrismQML has no pure-QML attached properties, so the span travels as
// a child-declared property and is read defensively here.
// 布局子项可自行声明可选整数 rowSpan / columnSpan (>= 1)；PrismQML 无纯 QML 附加
// 属性, 因此跨格数由子项属性承载, 并在此处做防御式读取。
function readSpan(item, name) {
    if (!item) return 1
    var value = item[name]
    if (typeof value !== "number" || !isFinite(value)) return 1
    var span = Math.floor(value)
    return span > 1 ? span : 1
}

function itemSpan(item) {
    return {
        rowSpan: readSpan(item, "rowSpan"),
        columnSpan: readSpan(item, "columnSpan")
    }
}

// Cell footprint: the cell cross extent follows the mode's uniform axis
// 单元格足迹: 单元格横向范围跟随该模式的统一轴
function footprintWidth(layout, item, originalSize, unitWidth) {
    var span = readSpan(item, "columnSpan")
    var base = unitWidth !== undefined && unitWidth !== null
        ? unitWidth : (originalSize ? originalSize.width : item.width)
    if (span <= 1) return base
    return span * base + (span - 1) * layout.spacing
}

function footprintHeight(layout, item, originalSize, unitHeight) {
    var span = readSpan(item, "rowSpan")
    var base = unitHeight !== undefined && unitHeight !== null
        ? unitHeight : (originalSize ? originalSize.height : item.height)
    if (span <= 1) return base
    return span * base + (span - 1) * layout.rowSpacing
}

function findBestSlidingPosition(heightMap, containerWidth, itemWidth, deque) {
    var maxX = containerWidth - itemWidth
    if (maxX < 0 || !isFinite(maxX)) return { x: 0, y: Infinity }
    if (itemWidth <= 0) return { x: 0, y: 0 }
    var lastX = Math.floor(maxX)
    var windowWidth = Math.ceil(itemWidth)
    var head = 0
    var tail = 0
    for (var index = 0; index < windowWidth; index++) {
        while (tail > head && heightMap[deque[tail - 1]] <= heightMap[index]) tail--
        deque[tail++] = index
    }
    var bestX = 0
    var bestY = heightMap[deque[head]]
    for (var x = 1; x <= lastX; x++) {
        while (head < tail && deque[head] < x) head++
        var nextIndex = x + windowWidth - 1
        while (tail > head && heightMap[deque[tail - 1]] <= heightMap[nextIndex]) tail--
        deque[tail++] = nextIndex
        var maxHeight = heightMap[deque[head]]
        if (maxHeight < bestY) {
            bestY = maxHeight
            bestX = x
        }
    }
    return { x: bestX, y: bestY }
}

function placeDefaultItem(layout, item, originalSize, heightMap,
                           containerWidth, useSlidingWindow, positionDeque) {
    var itemWidth = footprintWidth(layout, item, originalSize)
    var itemHeight = footprintHeight(layout, item, originalSize)
    var position = findBestPosition(
        heightMap, containerWidth, itemWidth, itemHeight,
        useSlidingWindow, positionDeque
    )
    item.x = position.x
    item.y = position.y
    item.width = itemWidth
    item.height = itemHeight
    var endX = Math.min(position.x + itemWidth, containerWidth)
    var newHeight = position.y + itemHeight + layout.rowSpacing
    for (var px = position.x; px < endX; px++) heightMap[px] = newHeight
    var gapEnd = Math.min(endX + layout.spacing, containerWidth)
    for (var gx = endX; gx < gapEnd; gx++) {
        heightMap[gx] = Math.max(heightMap[gx], newHeight)
    }
    return position.y + itemHeight
}

function appendDefaultItems(layout, defaultMode, slidingWindowMinItems) {
    if (!getState(layout, "layoutAppendable") || getState(layout, "layoutPending")
            || layout.mode !== defaultMode) return
    var items = getState(layout, "pendingAppendItems").slice(0)
    setState(layout, "pendingAppendItems", [])
    if (items.length === 0) return
    var containerWidth = Math.floor(layout.width)
    if (getState(layout, "defaultHeightMap").length !== containerWidth
            || getState(layout, "laidOutItemCount") + items.length
                !== getState(layout, "originalSizes").length) {
        layout._invalidateLayout()
        return
    }
    for (var check = 0; check < items.length; check++) {
        if (!layout._isLayoutChild(items[check])) {
            layout._invalidateLayout()
            return
        }
    }
    var heightMap = getState(layout, "defaultHeightMap").slice(0)
    var maxHeight = getState(layout, "defaultMaxHeight")
    var useSlidingWindow = usesSlidingWindow(
        layout, getState(layout, "originalSizes").length, slidingWindowMinItems
    )
    var positionDeque = useSlidingWindow ? [] : null
    for (var index = 0; index < items.length; index++) {
        maxHeight = Math.max(maxHeight, placeDefaultItem(
            layout, items[index],
            getState(layout, "originalSizes")[
                getState(layout, "laidOutItemCount") + index
            ],
            heightMap, containerWidth, useSlidingWindow, positionDeque
        ))
    }
    setState(layout, "laidOutItemCount",
        getState(layout, "laidOutItemCount") + items.length)
    setState(layout, "defaultHeightMap", heightMap)
    setState(layout, "defaultMaxHeight", maxHeight)
    setState(layout, "rowCount", 0)
    setState(layout, "rowHeights", [])
    layout.implicitHeight = maxHeight
}

function performLayout(layout, defaultMode, horizontalMode, verticalMode,
                       slidingWindowMinItems) {
    setState(layout, "layoutPending", false)
    setState(layout, "layoutAppendable", false)
    setState(layout, "laidOutItemCount", 0)
    setState(layout, "pendingAppendItems", [])

    if (layout.mode < 0 || layout.mode > 2) {
        console.warn("FlowLayout: Invalid mode value, falling back to default")
        layout.mode = defaultMode
        return
    }

    var children = layout._getVisibleChildren()
    if (children.length === 0 || layout.width <= 0) {
        layout.implicitHeight = 0
        setState(layout, "rowCount", 0)
        setState(layout, "rowHeights", [])
        return
    }

    switch (layout.mode) {
        case horizontalMode:
            layout.implicitHeight = layoutHorizontal(
                layout, children, slidingWindowMinItems
            )
            break
        case verticalMode:
            layout.implicitHeight = layoutVertical(layout, children)
            break
        default:
            layout.implicitHeight = layoutDefault(
                layout, children, slidingWindowMinItems
            )
    }
}

function layoutDefault(layout, children, slidingWindowMinItems) {
    if (children.length === 0) return 0
    var containerWidth = Math.floor(layout.width)
    var useSlidingWindow = usesSlidingWindow(
        layout, children.length, slidingWindowMinItems
    )
    var positionDeque = useSlidingWindow ? [] : null
    var heightMap = []
    for (var i = 0; i < containerWidth; i++) heightMap.push(0)

    var maxHeight = 0
    for (var index = 0; index < children.length; index++) {
        maxHeight = Math.max(maxHeight, placeDefaultItem(
            layout, children[index], getState(layout, "originalSizes")[index],
            heightMap, containerWidth, useSlidingWindow, positionDeque
        ))
    }
    setState(layout, "rowCount", 0)
    setState(layout, "rowHeights", [])
    setState(layout, "defaultHeightMap", heightMap)
    setState(layout, "defaultMaxHeight", maxHeight)
    setState(layout, "laidOutItemCount", children.length)
    setState(layout, "layoutAppendable", true)
    return maxHeight
}

function findBestPosition(heightMap, containerWidth, itemWidth,
                          itemHeight, useSlidingWindow, positionDeque) {
    if (useSlidingWindow) {
        return findBestSlidingPosition(
            heightMap, containerWidth, itemWidth, positionDeque || []
        )
    }

    var bestX = 0
    var bestY = Infinity
    var maxX = containerWidth - itemWidth
    for (var x = 0; x <= maxX; x++) {
        var maxHeight = 0
        var endX = Math.min(x + itemWidth, containerWidth)
        for (var index = x; index < endX; index++) {
            maxHeight = Math.max(maxHeight, heightMap[index])
        }
        if (maxHeight < bestY) {
            bestY = maxHeight
            bestX = x
        }
    }
    return { x: bestX, y: bestY }
}

function usesSlidingWindow(layout, itemTotal, slidingWindowMinItems) {
    return itemTotal >= slidingWindowMinItems
}

function layoutHorizontal(layout, children, slidingWindowMinItems) {
    var rows = calculateRows(layout, children)
    for (var band = 0; band < rows.length; band++) {
        rows[band].bandHeight = rowBandHeight(layout, rows[band])
    }
    var y = 0
    for (var r = 0; r < rows.length; r++) {
        var row = rows[r]
        var x = 0
        for (var i = 0; i < row.items.length; i++) {
            var item = row.items[i]
            var itemIndex = row.indices[i]
            var original = getState(layout, "originalSizes")[itemIndex]
            item.x = x
            item.y = y
            if (layout.preserveAspectRatio && original) {
                if (original.height > 0) {
                    var ratio = original.width / original.height
                    item.height = row.bandHeight
                    item.width = row.bandHeight * ratio
                }
            } else {
                item.height = row.bandHeight
                if (original) item.width = footprintWidth(layout, item, original)
            }
            x += item.width + layout.spacing
        }
        y += row.bandHeight + layout.rowSpacing
    }
    setState(layout, "rowCount", rows.length)
    setState(layout, "rowHeights",
        rows.map(function(row) { return row.bandHeight }))
    return rows.length > 0 ? y - layout.rowSpacing : 0
}

// Row band height: a rowSpan item raises its row band by whole row units
// 行带高度: rowSpan 子项把所在行带按行单位抬升, 因此不会与相邻行重叠
function rowBandHeight(layout, row) {
    var bandHeight = row.maxHeight
    for (var i = 0; i < row.items.length; i++) {
        var span = readSpan(row.items[i], "rowSpan")
        if (span > 1) {
            bandHeight = Math.max(
                bandHeight,
                span * row.maxHeight + (span - 1) * layout.rowSpacing
            )
        }
    }
    return bandHeight
}

function calculateRows(layout, children) {
    var rows = []
    var currentRow = { items: [], indices: [], maxHeight: 0, totalWidth: 0 }
    var x = 0
    for (var i = 0; i < children.length; i++) {
        var item = children[i]
        var originalSize = getState(layout, "originalSizes")[i]
        var itemWidth = footprintWidth(layout, item, originalSize)
        var itemHeight = originalSize ? originalSize.height : item.height
        if (x + itemWidth > layout.width && x > 0) {
            rows.push(currentRow)
            currentRow = { items: [], indices: [], maxHeight: 0, totalWidth: 0 }
            x = 0
        }
        currentRow.items.push(item)
        currentRow.indices.push(i)
        currentRow.maxHeight = Math.max(currentRow.maxHeight, itemHeight)
        currentRow.totalWidth = x + itemWidth
        x += itemWidth + layout.spacing
    }
    if (currentRow.items.length > 0) rows.push(currentRow)
    return rows
}

function layoutVertical(layout, children) {
    if (children.length === 0) return 0
    var columns = layout.columnCount > 0
        ? layout.columnCount : calculateAutoColumnCount(layout, children)
    if (columns <= 0) columns = 1
    var itemWidth = (layout.width - (columns - 1) * layout.spacing) / columns
    var columnHeights = []
    for (var c = 0; c < columns; c++) columnHeights.push(0)

    for (var i = 0; i < children.length; i++) {
        var item = children[i]
        var columnSpan = Math.min(readSpan(item, "columnSpan"), columns)
        var group = findShortestColumnGroup(columnHeights, columns, columnSpan)
        var originalSize = getState(layout, "originalSizes")[i]
        var originalHeight = originalSize ? originalSize.height : item.height
        var originalWidth = originalSize ? originalSize.width : item.width
        // A span wider than the grid is clamped to the available columns
        // 超过网格的跨格数会被约束到可用列数
        var spannedWidth = columnSpan > 1
            ? columnSpan * itemWidth + (columnSpan - 1) * layout.spacing
            : itemWidth
        var itemHeight
        if (layout.preserveAspectRatio && originalWidth > 0) {
            itemHeight = spannedWidth * (originalHeight / originalWidth)
        } else {
            itemHeight = footprintHeight(layout, item, originalSize)
        }
        item.x = group.start * (itemWidth + layout.spacing)
        item.y = group.height
        item.width = spannedWidth
        item.height = itemHeight
        var nextHeight = group.height + itemHeight + layout.rowSpacing
        for (var covered = group.start; covered < group.start + columnSpan; covered++) {
            columnHeights[covered] = nextHeight
        }
    }

    var maxHeight = 0
    for (var h = 0; h < columnHeights.length; h++) {
        maxHeight = Math.max(maxHeight, columnHeights[h])
    }
    setState(layout, "rowCount", columns)
    setState(layout, "rowHeights", columnHeights)
    return maxHeight > 0 ? maxHeight - layout.rowSpacing : 0
}

// Shortest column group: span 1 reproduces the historical shortest column pick
// 最短列组: span 为 1 时与历史的最短列选择完全一致
function findShortestColumnGroup(columnHeights, columns, span) {
    var bestStart = 0
    var bestHeight = Infinity
    var lastStart = Math.max(0, columns - span)
    for (var start = 0; start <= lastStart; start++) {
        var groupHeight = 0
        for (var index = start; index < start + span; index++) {
            if (columnHeights[index] > groupHeight) groupHeight = columnHeights[index]
        }
        if (groupHeight < bestHeight) {
            bestHeight = groupHeight
            bestStart = start
        }
    }
    return {
        start: bestStart,
        height: bestHeight === Infinity ? 0 : bestHeight
    }
}

function calculateAutoColumnCount(layout, children) {
    var maxWidth = 0
    var originalSizes = getState(layout, "originalSizes")
    for (var i = 0; i < originalSizes.length; i++) {
        if (originalSizes[i])
            maxWidth = Math.max(maxWidth, originalSizes[i].width)
    }
    if (maxWidth <= 0) maxWidth = 100
    return Math.max(
        1, Math.floor((layout.width + layout.spacing) / (maxWidth + layout.spacing))
    )
}
