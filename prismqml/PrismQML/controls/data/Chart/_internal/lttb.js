// LTTB (Largest Triangle Three Buckets) 降采样 — JS 端实现
// 另有同算法的 Python 版镜像实现, 两端逻辑保持一致.
//
// 把任意长序列降到 threshold 个代表点, 保留视觉趋势/峰谷.
// 原算法: Sveinn Steinarsson 2013
//
// 用法:
//   var indices = lttbIndices(xs, ys, 600);  // 返回保留的原始索引
//   var sampledLabels = indices.map(function(i) { return labels[i]; });
//   var sampledValues = indices.map(function(i) { return values[i]; });
//
// 多 series 共用同一组 indices 保证 X 轴对齐.

.pragma library

// xs: 单调递增的 x 轴数值数组 (传索引 [0, 1, 2, ...] 也行)
// ys: 同长度的主导 y 数组 (做 LTTB 选点用)
// threshold: 目标点数, ≥3 且 < n 才生效, 否则原样返回索引
function lttbIndices(xs, ys, threshold) {
    var n = xs.length;
    if (threshold >= n || threshold < 3) {
        var all = new Array(n);
        for (var i = 0; i < n; i++) all[i] = i;
        return all;
    }

    var bucketSize = (n - 2) / (threshold - 2);
    var out = [0];  // 第一点必留
    var a = 0;

    for (var i2 = 0; i2 < threshold - 2; i2++) {
        var bucketStart = Math.floor((i2 + 1) * bucketSize) + 1;
        var bucketEnd = Math.floor((i2 + 2) * bucketSize) + 1;
        if (bucketEnd > n - 1) bucketEnd = n - 1;
        if (bucketStart >= bucketEnd) continue;

        // 下一 bucket 的"平均点" — 三角形第三顶点
        var nextStart = bucketEnd;
        var nextEnd = Math.floor((i2 + 3) * bucketSize) + 1;
        if (nextEnd > n) nextEnd = n;
        var avgX, avgY;
        if (nextStart >= nextEnd) {
            avgX = xs[nextStart - 1];
            avgY = ys[nextStart - 1];
        } else {
            var sumX = 0, sumY = 0, cnt = nextEnd - nextStart;
            for (var j = nextStart; j < nextEnd; j++) {
                sumX += xs[j];
                sumY += ys[j];
            }
            avgX = sumX / cnt;
            avgY = sumY / cnt;
        }

        // 当前 bucket 里挑离 (a 点 → next_avg) 三角形面积最大的那个
        var ax = xs[a];
        var ay = ys[a];
        var maxArea = -1.0;
        var maxIdx = bucketStart;
        for (var jj = bucketStart; jj < bucketEnd; jj++) {
            var area = Math.abs(
                (ax - avgX) * (ys[jj] - ay) - (ax - xs[jj]) * (avgY - ay)
            );
            if (area > maxArea) {
                maxArea = area;
                maxIdx = jj;
            }
        }
        out.push(maxIdx);
        a = maxIdx;
    }

    out.push(n - 1);  // 最后一点必留
    return out;
}

// 按一组 indices 切一条 series
function applyIndices(indices, series) {
    var out = new Array(indices.length);
    for (var i = 0; i < indices.length; i++) out[i] = series[indices[i]];
    return out;
}
