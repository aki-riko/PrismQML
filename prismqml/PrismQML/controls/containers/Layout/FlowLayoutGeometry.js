// FlowLayoutGeometry - Flow layout geometry helpers 流式布局几何辅助
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

// findBestPosition - Find the leftmost lowest placement 查找最左侧最低放置位置
function findBestPosition(heightMap, containerWidth, itemWidth, deque) {
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
