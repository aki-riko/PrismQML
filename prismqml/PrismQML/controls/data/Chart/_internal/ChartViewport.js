// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

// ChartViewport - Viewport slicing and LTTB downsampling 视窗切片与 LTTB 降采样

.pragma library
.import "lttb.js" as Lttb

function indexArray(n) {
    var a = new Array(n)
    for (var i = 0; i < n; i++) a[i] = i
    return a
}

function valuesOf(arr) {
    var a = new Array(arr.length)
    for (var i = 0; i < arr.length; i++) {
        var it = arr[i]
        a[i] = (it && it.value !== undefined) ? it.value : 0
    }
    return a
}

function numbersOf(vals) {
    var a = new Array(vals.length)
    for (var i = 0; i < vals.length; i++) {
        a[i] = (typeof vals[i] === "number") ? vals[i] : 0
    }
    return a
}

function viewChartData(chartData, renderStart, renderEnd, threshold) {
    if (!chartData || chartData.length === 0) return []

    var src = chartData
    if (renderStart > 0 || renderEnd < 1) {
        var n = chartData.length
        var lo = Math.max(0, Math.floor(n * renderStart))
        var hi = Math.min(n, Math.ceil(n * renderEnd))
        if (hi <= lo) hi = Math.min(n, lo + 1)
        src = chartData.slice(lo, hi)
    }

    if (src.length <= threshold) return src

    var indices = Lttb.lttbIndices(indexArray(src.length), valuesOf(src), threshold)
    var out = new Array(indices.length)
    for (var i = 0; i < indices.length; i++) out[i] = src[indices[i]]
    return out
}

function viewSeries(series, renderStart, renderEnd, threshold) {
    if (!series || series.length === 0) return []

    var srcAll = series
    if (renderStart > 0 || renderEnd < 1) {
        var sliced = []
        for (var s = 0; s < series.length; s++) {
            var src = series[s] || {}
            var copy = {}
            for (var k in src) copy[k] = src[k]
            if (Array.isArray(src.values)) {
                var n = src.values.length
                var lo = Math.max(0, Math.floor(n * renderStart))
                var hi = Math.min(n, Math.ceil(n * renderEnd))
                if (hi <= lo) hi = Math.min(n, lo + 1)
                copy.values = src.values.slice(lo, hi)
            }
            if (Array.isArray(src.data)) {
                var n2 = src.data.length
                var lo2 = Math.max(0, Math.floor(n2 * renderStart))
                var hi2 = Math.min(n2, Math.ceil(n2 * renderEnd))
                if (hi2 <= lo2) hi2 = Math.min(n2, lo2 + 1)
                copy.data = src.data.slice(lo2, hi2)
            }
            sliced.push(copy)
        }
        srcAll = sliced
    }

    var maxLen = 0
    for (var s2 = 0; s2 < srcAll.length; s2++) {
        var v2 = srcAll[s2].values || srcAll[s2].data || []
        if (v2.length > maxLen) maxLen = v2.length
    }
    if (maxLen <= threshold) return srcAll

    var primary = srcAll[0].values || srcAll[0].data || []
    if (primary.length <= threshold) return srcAll

    var primIdx = Lttb.lttbIndices(indexArray(primary.length), numbersOf(primary), threshold)
    var out = []
    for (var s3 = 0; s3 < srcAll.length; s3++) {
        var c = {}
        for (var k2 in srcAll[s3]) c[k2] = srcAll[s3][k2]
        if (Array.isArray(srcAll[s3].values)) {
            c.values = primIdx.map(function(i) { return srcAll[s3].values[i] })
        }
        if (Array.isArray(srcAll[s3].data)) {
            c.data = primIdx.map(function(i) { return srcAll[s3].data[i] })
        }
        out.push(c)
    }
    return out
}
