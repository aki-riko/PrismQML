// ChartDataZoomFrame - Thumbnail draw-frame builder 缩略图绘制帧构建器
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// Turn the full data set into the cached thumbnail draw frame.
// 将全量数据转换为缓存的缩略图绘制帧。
// The leading series wins; chartData is the fallback when it carries no values.
// 优先使用主序列; 主序列没有数值时回退到 chartData。
function buildFrame(series, chartData) {
    var source = []
    if (series && typeof series.length === "number" && series.length > 0) {
        var first = series[0]
        if (first && first.values && typeof first.values.length === "number") {
            source = first.values
        }
    }
    if (source.length === 0 && chartData && typeof chartData.length === "number") {
        for (var i = 0; i < chartData.length; i++) {
            var item = chartData[i]
            source.push(item && item.value !== undefined ? item.value : 0)
        }
    }
    return normalize(source)
}

// Normalize raw values and derive the vertical extent. 归一化原始数值并推导纵向范围。
function normalize(values) {
    var normalized = []
    if (!values || typeof values.length !== "number" || values.length === 0) {
        return { values: normalized, minimum: 0, maximum: 0 }
    }
    var minimum = 0
    var maximum = 0
    for (var i = 0; i < values.length; i++) {
        var value = values[i]
        var normalizedValue = typeof value === "number" && isFinite(value)
                ? value : 0
        normalized.push(normalizedValue)
        if (i === 0 || normalizedValue < minimum) minimum = normalizedValue
        if (i === 0 || normalizedValue > maximum) maximum = normalizedValue
    }
    return { values: normalized, minimum: minimum, maximum: maximum }
}
