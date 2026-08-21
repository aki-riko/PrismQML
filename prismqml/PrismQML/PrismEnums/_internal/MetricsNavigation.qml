// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// MetricsNavigation - Sidebar overflow hint metrics 侧边栏溢出提示度量
//
// 侧边栏可滚动时的两种互补提示: 边缘渐隐说"还有更多", 浮层滚动轨说"还有多少、
// 你在哪"。两者参数都收在这里, 避免 Metrics.qml 继续膨胀。
// Two complementary overflow hints: the edge fade says "there is more", the
// overlay rail says "how much more, and where you are". Both live here so
// Metrics.qml does not keep growing.
QtObject {
    id: navigation

    // ==================== Required Props 必需属性 ====================
    // 由 Metrics 注入, 避免此处重复定义通用标尺 Injected by Metrics, no duplicate scales
    required property QtObject opacityScale
    required property QtObject durationScale
    required property int railInset
    required property int railBarWidth

    // ==================== Readonly State 只读状态 ====================
    readonly property QtObject fade: QtObject {
        // Fade band expressed in item heights; must span several items or the
        // per-item ramp collapses into a single visible step.
        // 渐隐带按项高倍数表达；必须跨多项，否则逐项斜坡会退化成单一档位。
        readonly property real bandItems: 2.0
        // Opacity an item reaches once fully inside the band 项完全进入渐隐带后的透明度
        readonly property real minOpacity: navigation.opacityScale.invisible
        // Opacity of an item clear of the band 项处于渐隐带之外时的透明度
        readonly property real maxOpacity: navigation.opacityScale.visible
    }

    readonly property QtObject rail: QtObject {
        // 轨道是浮层, 不占宽度, 不挤压导航项。
        // The rail is an overlay: it claims no width and never squeezes items.

        // Overlay inset from the viewport's right edge 浮层距视口右边缘的内缩
        readonly property int inset: navigation.railInset
        // Rail thickness; thinner than the standard bar because it floats
        // 轨道粗细; 因为是浮层, 比标准滚动条更细
        readonly property int thickness: navigation.railBarWidth - navigation.railInset
        // Opacity while idle 静止时的透明度
        readonly property real idleOpacity: navigation.opacityScale.invisible
        // Opacity while scrolling or hovering 滚动或悬停时的透明度
        readonly property real activeOpacity: navigation.opacityScale.visible
        // Reveal fast so the rail is present the moment the wheel turns
        // 快速淡入, 让轨道在滚轮转动的瞬间就在
        readonly property int revealDuration: navigation.durationScale.fast
        // Retreat gently so it does not snap away 平缓淡出, 不要突然消失
        readonly property int hideDuration: navigation.durationScale.slow
        // Idle delay before the rail retreats 轨道退隐前的静止延时
        readonly property int idleDelay: navigation.durationScale.verySlow
    }
}
