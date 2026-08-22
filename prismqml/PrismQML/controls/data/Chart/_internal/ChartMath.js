// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

// ChartMath - Pure series statistics shared by chart backends 图表后端共用的纯序列统计
//
// Side-effect free by contract: no Canvas, no QML state, no theme access.
// 契约上无副作用：不含 Canvas、QML 状态与主题访问。
// BarChartGeometry.js, LineChartPainter.js and LineChartMarkers.qml each carried
// their own copy of these two functions; this is now the single owner.
// 三处各持一份副本，现由本文件单一归属。

.pragma library

// Arithmetic mean; empty or missing input yields 0.
// 算术平均值；空输入或缺失输入返回 0。
function average(values) {
    if (!values || values.length === 0) return 0
    var sum = 0
    for (var index = 0; index < values.length; index++) sum += values[index]
    return sum / values.length
}

// First index of the smallest and largest value.
// 最小值与最大值的首个下标。
// Empty or missing input yields indices -1 and values 0, so callers can treat
// -1 as "no marker". 空输入或缺失输入返回下标 -1 与值 0，调用方可用 -1 表示无标记。
function findMinMaxIndices(values) {
    if (!values || values.length === 0) {
        return { minIdx: -1, maxIdx: -1, minVal: 0, maxVal: 0 }
    }
    var minIdx = 0
    var maxIdx = 0
    for (var index = 1; index < values.length; index++) {
        if (values[index] < values[minIdx]) minIdx = index
        if (values[index] > values[maxIdx]) maxIdx = index
    }
    return {
        minIdx: minIdx, maxIdx: maxIdx,
        minVal: values[minIdx], maxVal: values[maxIdx]
    }
}
