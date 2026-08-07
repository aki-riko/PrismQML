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

function projectChartData(chartData, renderStart, renderEnd, threshold,
                          preferredSource) {
    if (!chartData || chartData.length === 0) {
        return { data: [], sourceLength: 0, sourceOffset: 0, sourceIndices: [] }
    }

    var range = bounds(chartData.length, renderStart, renderEnd)
    var preferredIndices = preferredSource &&
        preferredSource.sourceLength === chartData.length
        ? preferredSource.sourceIndices : null
    if (preferredIndices && typeof preferredIndices.length === "number" &&
            preferredIndices.length > 0) {
        var aligned = new Array(preferredIndices.length)
        for (var alignedIndex = 0;
                alignedIndex < preferredIndices.length; alignedIndex++) {
            aligned[alignedIndex] = chartData[preferredIndices[alignedIndex]]
        }
        return {
            data: aligned,
            sourceLength: chartData.length,
            sourceOffset: range.lo,
            sourceIndices: Array.prototype.slice.call(preferredIndices)
        }
    }
    if (range.length <= threshold) {
        return {
            data: range.length === chartData.length
                ? chartData
                : chartData.slice(range.lo, range.hi),
            sourceLength: chartData.length,
            sourceOffset: range.lo,
            sourceIndices: []
        }
    }

    var indices = Lttb.lttbRangeIndices(
        chartData, range.lo, range.hi, threshold, true
    )
    var out = new Array(indices.length)
    var sourceIndices = new Array(indices.length)
    for (var i = 0; i < indices.length; i++) {
        out[i] = chartData[range.lo + indices[i]]
        sourceIndices[i] = range.lo + indices[i]
    }
    return {
        data: out,
        sourceLength: chartData.length,
        sourceOffset: range.lo,
        sourceIndices: sourceIndices
    }
}

function viewChartData(chartData, renderStart, renderEnd, threshold) {
    return projectChartData(chartData, renderStart, renderEnd, threshold).data
}

function projectSeries(series, renderStart, renderEnd, threshold) {
    if (!series || series.length === 0) {
        return { data: [], valueSources: [], dataSources: [] }
    }

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
    var valueSources = []
    var dataSources = []
    for (var s2 = 0; s2 < series.length; s2++) {
        var c = {}
        var source = series[s2] || {}
        for (var key in source) c[key] = source[key]
        if (source.values && typeof source.values.length === "number") {
            var valueBounds = bounds(source.values.length, renderStart, renderEnd)
            var valueIndices = []
            c.values = indices
                ? indices.map(function(i) {
                    valueIndices.push(valueBounds.lo + i)
                    return source.values[valueBounds.lo + i]
                })
                : Array.prototype.slice.call(source.values, valueBounds.lo, valueBounds.hi)
            valueSources.push({
                sourceLength: source.values.length,
                sourceOffset: valueBounds.lo,
                sourceIndices: valueIndices
            })
        } else {
            valueSources.push({ sourceLength: 0, sourceOffset: 0, sourceIndices: [] })
        }
        if (source.data && typeof source.data.length === "number") {
            var dataBounds = bounds(source.data.length, renderStart, renderEnd)
            var dataIndices = []
            c.data = indices
                ? indices.map(function(i) {
                    dataIndices.push(dataBounds.lo + i)
                    return source.data[dataBounds.lo + i]
                })
                : Array.prototype.slice.call(source.data, dataBounds.lo, dataBounds.hi)
            dataSources.push({
                sourceLength: source.data.length,
                sourceOffset: dataBounds.lo,
                sourceIndices: dataIndices
            })
        } else {
            dataSources.push({ sourceLength: 0, sourceOffset: 0, sourceIndices: [] })
        }
        out.push(c)
    }
    return { data: out, valueSources: valueSources, dataSources: dataSources }
}

function viewSeries(series, renderStart, renderEnd, threshold) {
    return projectSeries(series, renderStart, renderEnd, threshold).data
}
