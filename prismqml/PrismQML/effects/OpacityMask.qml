// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// OpacityMask - Opacity mask effect 透明度遮罩
// Replaces Qt5Compat.GraphicalEffects.OpacityMask 替代Qt5Compat
//
// VERIFIED LIMIT (Qt 6.11.2): MultiEffect masking is a **silent no-op** when this effect is
// installed through layer.effect. Every wiring was measured against real rendered pixels
// (inline mask child, property-assigned mask, ShaderEffectSource, parked layered mask) and
// all produced output identical to having no mask at all. Only the standalone form works,
// and only with a hard-edged (binary) mask:
//   OpacityMask { source: someItem; mask: maskItem }
// The mask item must be visible with layer.enabled: true — an invisible mask item never
// bakes its layer texture, so the mask is silently ignored. It may sit outside the window
// so it is never painted. Continuous-alpha (gradient) masks do not produce a proportional
// fade: the mask behaves as a threshold gate, not as an alpha multiplier.
// 实测限制 (Qt 6.11.2): 经 layer.effect 安装时 MultiEffect 遮罩**静默失效**——内联遮罩子项、
// 属性赋值遮罩、ShaderEffectSource、停靠分层遮罩四种接线都对真实渲染像素验证过, 输出与
// 完全不挂遮罩一致。只有独立写法 + 硬边(二值)遮罩生效, 且遮罩项必须 visible 且开启
// layer.enabled(不可见则层纹理不会烘焙, 遮罩被静默忽略), 可以停在窗口之外避免被绘制。
// 渐变(连续 alpha)遮罩不会产生按比例的淡出: 遮罩是阈值门, 不是 alpha 乘法器。
//
// Usage 1 - as layer.effect 作为layer.effect使用: **NOT SUPPORTED** in Qt 6.11 (see above)
// Usage 2 - as standalone component 作为独立组件使用: works with a binary mask 二值遮罩可用

MultiEffect {
    id: root

    // ==================== Public Props 公开属性 ====================
    property var mask: null
    property bool invert: false

    // ==================== Content 内容 ====================
    // Only enable when mask exists 仅有mask时启用
    maskEnabled: root.mask !== null
    maskSource: root.mask
    maskInverted: root.invert
    // Keep regular masks at Qt's default threshold; inverted spotlight masks need the midpoint mapping
    // 普通蒙版保留 Qt 默认阈值；仅反向聚光蒙版使用中点映射
    maskThresholdMin: root.invert ? 0.5 : 0.0
    maskSpreadAtMin: 1.0
}
