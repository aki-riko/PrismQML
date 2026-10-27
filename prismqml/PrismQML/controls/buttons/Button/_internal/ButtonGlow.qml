// ButtonGlow - Bloom halo bound to a ButtonCore 绑定到 ButtonCore 的泛光光晕
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../../effects"

// ButtonGlow - Button-side adapter for the shared GlowHalo effect 共享 GlowHalo 效果的按钮侧适配层
//
// Glow itself is a reusable decoration owned by `effects/GlowHalo` and enumerated
// by `Enums.glow`; this module only binds it to a ButtonCore's state (pointer
// states, countdown, skin elevation policy, reduced motion). Keeping the binding
// here means the shared effect never has to know about button internals.
// 泛光本体是 `effects/GlowHalo` 提供的可复用装饰, 枚举由 `Enums.glow` 承载; 本模块
// 只负责把它绑定到 ButtonCore 的状态(指针态、倒计时、皮肤悬浮策略、减少动态效果)。
// 绑定留在这里, 使共享效果无需了解按钮内部。
//
// Created imperatively by ButtonSurface so a button that never requests glow pays
// no resident object cost. 由 ButtonSurface 以命令式创建, 因此从不请求泛光的按钮
// 不承担常驻对象开销。
GlowHalo {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property var button

    // ==================== Readonly State 只读状态 ====================
    readonly property var _skin: button.effectiveSkinContext
    readonly property var _tokens: _skin.glow

    // ==================== Content 内容 ====================
    // The bloom follows the resolved face hue, so it composes with every fill
    // style: accent blooms blue, a filled success button blooms green, and a
    // neutral default button blooms pale. A flat face has no fill, so it falls back
    // to the accent hue instead of blooming from a transparent face.
    // 泛光跟随已解析的面色相, 因此可与所有填充样式组合: 主色泛蓝、成功后填充泛绿、
    // 中性默认泛浅。扁平面无填充, 因此回退到主色而不是从透明面泛光。
    target: button
    haloColor: button.flat ? _skin.accentColor : button._effectiveBgColor
    tokens: _tokens
    // Ticket paper is square and shadowless by design, so its policy reports a zero
    // ratio and the halo collapses instead of fighting that skin.
    // 票据纸面按设计是直角无阴影, 因此其策略报零, 光晕收敛而不是与该皮肤冲突。
    spreadRatio: _skin.isVintageTicket ? 0 : _tokens.spreadRatio
    blurRatio: _skin.isVintageTicket ? 0 : _tokens.blurRatio
    active: button._glowActive && !button.flat
    pulseEnabled: !button._countdownActive
    pressed: button.pressed
    highlighted: button._touchActive
    enabledState: button._styleEffectiveEnabled
    reduceMotion: _skin.reduceMotion
}
