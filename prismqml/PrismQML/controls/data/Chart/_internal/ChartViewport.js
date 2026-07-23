// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

// ChartViewport - Viewport slicing and LTTB downsampling 视窗切片与 LTTB 降采样

.pragma library
.import "lttb.js" as Lttb

function bounds(length, renderStart, renderEnd) {
    var lo = 0
    var hi = length
    if (renderStart > 0 || renderEnd < 1) {
        lo = Math.max(0, Math.floor(length * renderStart))
        hi = Math.min(length, Math.ceil(length * renderEnd))
        if (hi <= lo) hi = Math.min(length, lo + 1)
    }
    return { lo: lo, hi: hi, length: hi - lo }
}

function viewChartData(chartData, renderStart, renderEnd, threshold) {
    if (!chartData || chartData.length === 0) return []

    var range = bounds(chartData.length, renderStart, renderEnd)
    if (range.length <= threshold) {
        return range.length === chartData.length
            ? chartData
            : chartData.slice(range.lo, range.hi)
    }

    var indices = Lttb.lttbRangeIndices(
        chartData, range.lo, range.hi, threshold, true
    )
    var out = new Array(indices.length)
    for (var i = 0; i < indices.length; i++) {
        out[i] = chartData[range.lo + indices[i]]
    }
    return out
}

function viewSeries(series, renderStart, renderEnd, threshold) {
    if (!series || series.length === 0) return []

    var maxLen = 0
    for (var s = 0; s < series.length; s++) {
        var source = series[s] || {}
        var values = source.values && typeof source.values.length === "number"
                     ? source.values
                     : (source.data && typeof source.data.length === "number" ? source.data : [])
        var valueRange = bounds(values.length, renderStart, renderEnd)
        if (valueRange.length > maxLen) maxLen = valueRange.length
    }

    var primarySource = series[0] || {}
    var primary = primarySource.values && typeof primarySource.values.length === "number"
                  ? primarySource.values
                  : (primarySource.data && typeof primarySource.data.length === "number" ? primarySource.data : [])
    var primaryRange = bounds(primary.length, renderStart, renderEnd)
    var indices = null
    if (maxLen > threshold && primaryRange.length > threshold) {
        indices = Lttb.lttbRangeIndices(
            primary, primaryRange.lo, primaryRange.hi, threshold, false
        )
    }

    var out = []
    for (var s2 = 0; s2 < series.length; s2++) {
        var c = {}
        var source = series[s2] || {}
        for (var key in source) c[key] = source[key]
        if (source.values && typeof source.values.length === "number") {
            var valueBounds = bounds(source.values.length, renderStart, renderEnd)
            c.values = indices
                ? indices.map(function(i) { return source.values[valueBounds.lo + i] })
                : Array.prototype.slice.call(source.values, valueBounds.lo, valueBounds.hi)
        }
        if (source.data && typeof source.data.length === "number") {
            var dataBounds = bounds(source.data.length, renderStart, renderEnd)
            c.data = indices
                ? indices.map(function(i) { return source.data[dataBounds.lo + i] })
                : Array.prototype.slice.call(source.data, dataBounds.lo, dataBounds.hi)
        }
        out.push(c)
    }
    return out
}
