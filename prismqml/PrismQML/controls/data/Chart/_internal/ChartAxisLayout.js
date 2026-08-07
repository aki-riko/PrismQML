// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// Return a stable pixel width for one axis label 返回单个坐标轴标签的稳定像素宽度
function textWidth(fontMetrics, value) {
    if (!fontMetrics) return 0
    return Math.ceil(fontMetrics.advanceWidth(value === undefined || value === null
                                              ? "" : String(value)))
}

// Measure the widest label in a collection 测量标签集合中的最大宽度
function maximumTextWidth(fontMetrics, values) {
    var labels = values && typeof values.length === "number" ? values : []
    var maximum = 0
    for (var index = 0; index < labels.length; index++) {
        maximum = Math.max(maximum, textWidth(fontMetrics, labels[index]))
    }
    return maximum
}

// Keep an automatically measured axis between its visual safety bounds 将自动测量的坐标轴限制在安全视觉范围内
function boundedAxisWidth(fontMetrics, values, minimumWidth, maximumWidth, horizontalPadding) {
    var measured = maximumTextWidth(fontMetrics, values) + horizontalPadding
    return Math.max(minimumWidth, Math.min(maximumWidth, measured))
}

// Calculate how many category slots one complete label needs 计算完整分类标签需要跨越的槽位数
function categoryStride(fontMetrics, values, slotWidth, minimumGap) {
    if (!values || values.length <= 1 || slotWidth <= 0) return 1
    var requiredWidth = maximumTextWidth(fontMetrics, values) + minimumGap
    return Math.max(1, Math.ceil(requiredWidth / slotWidth))
}

// Preserve the first and last labels while keeping sampled labels separated 保留首尾标签并确保抽样标签互不重叠
function categoryLabelVisible(index, count, stride) {
    if (count <= 0) return false
    if (stride <= 1 || count <= 2) return true
    if (index === 0 || index === count - 1) return true
    return index % stride === 0 && count - 1 - index >= stride
}

// Allocate enough width for a sampled label without exceeding the axis 分配完整抽样标签宽度且不超出坐标轴
function categoryLabelWidth(fontMetrics, value, slotWidth, stride, minimumGap, axisWidth) {
    var available = Math.min(axisWidth, Math.max(slotWidth, slotWidth * stride - minimumGap))
    return Math.min(textWidth(fontMetrics, value), Math.max(0, available))
}

// Center a label on its tick and clamp it inside the axis 将标签居中到刻度并限制在坐标轴内部
function clampedCenteredX(centerX, labelWidth, axisWidth) {
    return Math.max(0, Math.min(centerX - labelWidth / 2, Math.max(0, axisWidth - labelWidth)))
}
