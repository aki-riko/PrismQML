// FuzzyMatcher.js
// fzf 风格子序列模糊匹配 — query 字符按顺序在 text 中查找,允许不连续.
//
// 评分加权:
//   - prefix(从首字符开始)        +10
//   - 紧凑(连续无间隔)            +5/字符
//   - title 字段权重              ×3
//   - subtitle / section 字段     ×2
//   - keywords 字段               ×1
//
// 公开 API:
//   match(query, text)                           → { score, ranges } | null
//   matchEntry(query, entry, matchKeys, weights) → { score, fieldRanges } | null
//   substringMatch(query, text)                  → { score, ranges } | null
//
// 调用方拿到 ranges 数组(每项是 [start, endExclusive])用于高亮渲染.
// matchEntry 返回 fieldRanges 是 { fieldName: [[start, end], ...] }.

.pragma library

// ============ 内部辅助 ============

// 大小写归一(英文转小写,中文/其他保持)
function _normalize(s) {
    return (s || "").toLowerCase()
}

// ============ 公开 API ============

// 子序列匹配
// query='cat', text='concatenate' → 命中 c[0] a[3] t[4],ranges=[[0,1],[3,5]]
// 失败返回 null
function match(query, text) {
    if (!query || !text) {
        return query ? null : { score: 0, ranges: [] }
    }
    var q = _normalize(query)
    var t = _normalize(text)

    var ranges = []
    var qi = 0
    var lastMatchedIdx = -1
    var matchStart = -1
    var consecutiveBonus = 0
    var prefixBonus = 0
    var compactBonus = 0

    for (var ti = 0; ti < t.length && qi < q.length; ti++) {
        if (t[ti] === q[qi]) {
            // prefix bonus: 第一个 query 字符落在 text[0]
            if (qi === 0 && ti === 0) {
                prefixBonus = 10
            }
            // 连续匹配奖励 (lastMatchedIdx >= 0 保证有前驱命中,避免 ti=0 时 ti-1=-1 误中)
            if (lastMatchedIdx >= 0 && lastMatchedIdx === ti - 1) {
                consecutiveBonus++
                compactBonus += 5
                ranges[ranges.length - 1][1] = ti + 1
            } else {
                ranges.push([ti, ti + 1])
                consecutiveBonus = 0
            }
            lastMatchedIdx = ti
            qi++
        }
    }

    if (qi < q.length) {
        return null  // query 没全部命中,匹配失败
    }

    // 基础分: 命中字符数(归一后) - 间隔惩罚
    var totalGap = lastMatchedIdx - ranges[0][0] - q.length + 1
    var score = q.length * 10 - totalGap + prefixBonus + compactBonus

    return { score: score, ranges: ranges }
}

// 字符串包含匹配(降级版)
function substringMatch(query, text) {
    if (!query) return { score: 0, ranges: [] }
    if (!text) return null
    var q = _normalize(query)
    var t = _normalize(text)
    var idx = t.indexOf(q)
    if (idx < 0) return null
    var prefixBonus = idx === 0 ? 10 : 0
    return {
        score: q.length * 10 + prefixBonus,
        ranges: [[idx, idx + q.length]]
    }
}

// 在 entry 多个字段上匹配,返回最高分组合
// matchKeys: ['title', 'subtitle', 'keywords'] 等,默认 ['title', 'subtitle', 'keywords']
// weights:   { title: 3, subtitle: 2, section: 2, keywords: 1 } 默认值
// 返回 { score, fieldRanges: { title?: ranges, subtitle?: ranges, ... } } | null
function matchEntry(query, entry, matchKeys, weights, useFuzzy) {
    if (!entry) return null
    if (!query) return { score: 0, fieldRanges: {} }

    var keys = matchKeys || ['title', 'subtitle', 'keywords']
    var w = weights || { title: 3, subtitle: 2, section: 2, keywords: 1 }
    var matcher = (useFuzzy === false) ? substringMatch : match

    var totalScore = 0
    var fieldRanges = {}
    var anyMatch = false

    for (var i = 0; i < keys.length; i++) {
        var key = keys[i]
        var val = entry[key]
        if (val === undefined || val === null) continue

        var weight = w[key] !== undefined ? w[key] : 1

        if (Array.isArray(val)) {
            // keywords 等数组字段: 取最佳一项命中
            var bestArrScore = 0
            var bestArrRanges = null
            for (var j = 0; j < val.length; j++) {
                var r = matcher(query, String(val[j]))
                if (r && r.score > bestArrScore) {
                    bestArrScore = r.score
                    bestArrRanges = r.ranges
                }
            }
            if (bestArrRanges !== null) {
                anyMatch = true
                totalScore += bestArrScore * weight
                // keywords 不需要 ranges 渲染(不显示),但记录方便调试
                fieldRanges[key] = bestArrRanges
            }
        } else {
            var r2 = matcher(query, String(val))
            if (r2) {
                anyMatch = true
                totalScore += r2.score * weight
                fieldRanges[key] = r2.ranges
            }
        }
    }

    if (!anyMatch) return null
    return { score: totalScore, fieldRanges: fieldRanges }
}

// 过滤一组 entry 并按 score 降序排序
// 返回 [{ entry, score, fieldRanges }, ...]
function filterAndRank(query, entries, matchKeys, weights, useFuzzy, maxResults) {
    if (!entries || entries.length === 0) return []
    if (!query) {
        // 空查询: 返回全部(或裁前 maxResults)
        var out = []
        for (var i = 0; i < entries.length; i++) {
            out.push({ entry: entries[i], score: 0, fieldRanges: {} })
            if (maxResults > 0 && out.length >= maxResults) break
        }
        return out
    }

    var hits = []
    for (var k = 0; k < entries.length; k++) {
        var m = matchEntry(query, entries[k], matchKeys, weights, useFuzzy)
        if (m !== null) {
            hits.push({ entry: entries[k], score: m.score, fieldRanges: m.fieldRanges })
        }
    }

    hits.sort(function(a, b) { return b.score - a.score })

    if (maxResults > 0 && hits.length > maxResults) {
        hits = hits.slice(0, maxResults)
    }
    return hits
}
