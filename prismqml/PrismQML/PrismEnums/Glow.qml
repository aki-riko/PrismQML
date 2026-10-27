// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Glow - Shared bloom-halo enum and tokens 共享泛光光晕枚举与令牌
//
// Glow is a decoration, not a component state: it paints a soft bloom around
// whatever surface it is attached to, so the same axis serves buttons, cards,
// chips, or any future rect. Components opt in through their own public
// `glow` property, whose default must stay `glow_none`.
// 泛光是装饰而非组件状态: 它环绕所附着的表面绘制柔和光晕, 因此同一套轴可供按钮、
// 卡片、Chip 或任何未来的矩形使用。组件通过各自的公开 `glow` 属性启用, 默认值必须
// 保持 `glow_none`。
//
// The halo colour is supplied by the consumer (normally its resolved face colour)
// rather than read here, because only the consumer knows what it painted.
// 光晕颜色由使用者提供(通常是其已解析面色), 而不是在此读取, 因为只有使用者知道
// 自己画了什么。
QtObject {
    // ==================== Enum 枚举 ====================
    readonly property int glow_none: 0              // No bloom 无泛光
    readonly property int glow_accent: 1            // Face-following bloom 跟随所附着表面的泛光

    // ==================== Geometry 几何 ====================
    // Sized as a ratio of the target's short edge, not in absolute pixels: a fixed
    // spread that looks right on a 46 px button swallows a 32 px one. Measured on a
    // real D3D11 window, this ratio puts the visible band at about a quarter of the
    // face height with a peak tint of ~25/255, which reads as a soft rim.
    // 按目标短边的比例而不是绝对像素定尺: 在 46 像素按钮上合适的固定外扩会把 32 像素
    // 目标整个吞掉。真实 D3D11 窗口实测显示, 该比例让可见带约为面高的四分之一, 峰值
    // 着色约 25/255, 读作柔和描边。
    readonly property real blurRatio: 0.45          // Falloff width as a share of the short edge 衰减宽度占短边比例
    readonly property real spreadRatio: 0.10        // Outward growth as a share of the short edge 外扩占短边比例

    // ==================== Strength 强度 ====================
    // Resting alpha at full strength; the state multipliers below scale it.
    // 满强度下的静息 alpha; 下方状态倍数对其进行缩放。
    readonly property real restAlpha: 0.26
    readonly property real hoverStrength: 1.3       // Hover multiplier 悬浮强度倍数
    readonly property real pressedStrength: 0.85    // Press multiplier 按压强度倍数
    // A disabled/loading surface keeps a faint static ember instead of dropping to
    // nothing, so state changes read as the light dimming rather than the halo
    // popping in and out. 禁用/加载表面保留微弱静态余辉而不是完全消失, 使状态切换
    // 读作"灯光变暗"而非光晕突兀闪现。
    readonly property real disabledStrength: 0.3

    // ==================== Pulse 呼吸 ====================
    readonly property real pulseMin: 0.72           // Breathing floor 呼吸下限
    readonly property real pulseMax: 1.0            // Breathing ceiling 呼吸上限
    readonly property int breatheDuration: 1700     // Half-cycle duration 呼吸半程时长
}
