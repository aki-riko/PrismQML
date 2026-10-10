// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Motion - Fluent 2 motion tokens 动效令牌
// Stage 1 scope: tokens only. No existing component consumes them yet, and the
// existing inline Easing usages stay untouched until stage 2 migrates them.
// 阶段一范围：仅新增令牌。既有组件尚未消费，既有内联 Easing 留待阶段二迁移。
QtObject {
    id: root

    // Injected by Enums 由 Enums 注入
    property var durations: null      // Metrics.duration source 度量时长来源
    property bool reduceMotion: false // Reduced-motion switch 减少动态效果开关

    // Degenerate source used only before Metrics injection; all zeros mean
    // "no animation", never a fabricated duration. 仅在 Metrics 注入前使用的
    // 退化来源；全零表示无动画，不伪造时长。
    readonly property QtObject _zeroDurations: QtObject {
        readonly property int ultraFast: 0
        readonly property int fast: 0
        readonly property int normal: 0
        readonly property int medium: 0
        readonly property int slow: 0
        readonly property int slower: 0
    }
    readonly property var _source: root.durations !== null ? root.durations : root._zeroDurations

    // Resolve one base duration through the reduced-motion switch.
    // 按减少动态效果开关解析单个基础时长。
    function resolveDuration(milliseconds) {
        return root.reduceMotion ? 0 : milliseconds
    }

    // ==================== Easing 缓动曲线 ====================
    // Fluent 2 standard curves. Qt consumes cubic-bezier control points through
    // easing.type: Easing.BezierSpline plus easing.bezierCurve: [...]; the
    // trailing 1, 1 is Qt's fixed end point, not a Fluent token.
    // Fluent 2 标准曲线。Qt 通过 easing.type: Easing.BezierSpline 与
    // easing.bezierCurve: [...] 消费三次贝塞尔控制点；末尾 1, 1 是 Qt 固定终点，
    // 不属于 Fluent 令牌。
    readonly property int easingType: Easing.BezierSpline
    readonly property QtObject curve: QtObject {
        readonly property var standard: [0.8, 0, 0.2, 1, 1, 1]     // cubic-bezier(0.8, 0, 0.2, 1) Standard 标准
        readonly property var decelerate: [0.1, 0.9, 0.2, 1, 1, 1] // cubic-bezier(0.1, 0.9, 0.2, 1) Decelerate 减速
        readonly property var accelerate: [0.7, 0, 1, 0.5, 1, 1]   // cubic-bezier(0.7, 0, 1, 0.5) Accelerate 加速
    }

    // ==================== Duration Aliases 时长语义别名 ====================
    // Fluent 2 semantic aliases resolved from Metrics.duration so no duration is
    // duplicated here; every alias collapses to 0 while reduceMotion is on.
    // Fluent 2 语义别名解析自 Metrics.duration，此处不复制任何时长数值；
    // reduceMotion 开启时全部别名解析为 0。
    readonly property QtObject duration: QtObject {
        readonly property int ultraFast: root.resolveDuration(root._source.ultraFast)
        readonly property int faster: root.resolveDuration(root._source.fast)
        readonly property int fast: root.resolveDuration(root._source.normal)
        readonly property int normal: root.resolveDuration(root._source.medium)
        readonly property int gentle: root.resolveDuration(root._source.slow)
        readonly property int slow: root.resolveDuration(root._source.slower)
    }
}
