// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// Conclusion gate 结论门
//
// Gutters exist only to answer "does the content overflow the viewport?". A
// virtual view keeps refining content extents while scrolling, so every
// correction used to re-run the whole remove/measure/restore round: each round
// toggles the target's gutter margin, which re-lays out every visible delegate,
// rewraps text and feeds yet another content range back in. When the refined
// range cannot change the answer, skipping the round is not a shortcut on the
// measurement, it is the same conclusion without the churn.
// 避让槽的唯一目的是回答「内容是否溢出视口」。虚拟视图滚动时会持续修正内容
// 范围，过去每一版修正都会重跑整轮「撤槽/测量/复槽」：每轮都翻转目标的避让
// 边距，迫使全部可见委托重新排版、文本重换行，并回吐新的内容范围。当修正后
// 的范围无法改变结论时，跳过该轮不是测量上的取巧，而是同一结论下的无谓重排。
function keepsConclusion(host) {
    var target = host.target
    // A running transaction and a missing target are never gated.
    // 进行中的事务与缺失的目标永不进入结论门。
    if (host._destroying || host._updatePending || !target) return false
    // A viewport resize is a geometry change, not a content estimate.
    // 视口变尺是几何变化而非内容估算。
    if (target.width !== host._lastTargetWidth
            || target.height !== host._lastTargetHeight) return false
    // Disabled scroll bars are normalised by scheduleUpdate(); let it run.
    // 关闭滚动条由 scheduleUpdate() 统一归一化，交给它执行。
    if (!host.scrollBarsEnabled) return false
    // Virtual views commit their layout lazily: ListView/GridView can hold a
    // stale content extent and stay silent until a layout pass runs, so the
    // range may only be read after committing that pass. This is the same
    // contract the gutter measurement follows, and it is what keeps a cleared
    // model from being judged by its previous extent.
    // 虚拟视图的布局是延迟提交的：ListView/GridView 在布局运行前会保留过期的内容
    // 范围且不发信号，因此必须先提交布局再读取范围。这与避让槽测量遵循同一约定，
    // 也正是「模型已清空却按旧范围判定」的防线。
    if (typeof target.forceLayout === "function") target.forceLayout()
    var verticalEmpty = host.itemCount === 0 && !host.alwaysShowVertical
    var horizontalEmpty = host.itemCount === 0 && !host.alwaysShowHorizontal
    // Mirror the committed conclusion formulas exactly, and require both axes
    // to agree: an overflow on the other axis may still flip, so one stable
    // axis never licenses skipping the round.
    // 与已提交结论的公式逐项对齐，并要求两轴同时一致：另一轴的溢出仍可能翻转，
    // 单轴稳定不足以跳过本轮重测。
    var vertical = !verticalEmpty && host.scrollBarsEnabled && host.verticalEnabled
        && (host.alwaysShowVertical || target.contentHeight > target.height)
    var horizontal = !horizontalEmpty && host.scrollBarsEnabled
        && host.horizontalEnabled
        && (host.alwaysShowHorizontal || target.contentWidth > target.width)
    return vertical === host._needsVertical
        && horizontal === host._needsHorizontal
}
