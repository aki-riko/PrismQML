// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// ButtonStyleHelper - Button color calculation 按钮颜色计算
// Extracts complex color logic from ButtonCore 从ButtonCore提取复杂颜色逻辑
QtObject {
    id: helper
    
    // ==================== Required Props 必需属性 ====================
    required property int style
    required property int level
    required property bool controlEnabled
    required property bool loading
    required property bool countdownActive
    required property bool hovered
    required property bool pressed
    required property bool isToggleChecked

    // ==================== Readonly State 只读状态 ====================
    readonly property bool effectiveEnabled: controlEnabled && !loading && !countdownActive

    // Background color 背景色
    readonly property color bgColor: {
        if (!Enums || !Enums.stateColor) return Enums.stateColor.controlBg


        if (isToggleChecked) {
            if (style === Enums.button.style_primary) {
                if (!effectiveEnabled) return Enums.isVintageTicket
                    ? Enums.stateColor.disabledBg : Enums.stateColor.disabled
                if (pressed) return Enums.stateColor.controlBgPressed
                if (hovered) return Enums.stateColor.controlBgHover
                return Enums.cardColor
            }
            if (!effectiveEnabled) return Enums.isVintageTicket
                ? Enums.stateColor.disabledBg : Enums.stateColor.disabled
            if (pressed) return Qt.darker(Enums.accentColor, 1.1)
            if (hovered) return Qt.lighter(Enums.accentColor, 1.1)
            return Enums.accentColor
        }
        
        switch (style) {
            case Enums.button.style_primary:
                if (!effectiveEnabled) return Enums.stateColor.primaryDisabled
                if (pressed) return Qt.darker(Enums.accentColor, 1.1)
                if (hovered) return Qt.lighter(Enums.accentColor, 1.1)
                return Enums.accentColor
            case Enums.button.style_transparent:
                if (!effectiveEnabled) return Enums.stateColor.controlBgTransparent
                if (pressed) return Enums.stateColor.transparentPressed
                if (hovered) return Enums.stateColor.transparentHover
                return Enums.stateColor.controlBgTransparent
            case Enums.button.style_text:
            case Enums.button.style_hyperlink:
                if (!effectiveEnabled) return Enums.stateColor.controlBgTransparent
                if (pressed) return Enums.stateColor.transparentPressed
                if (hovered) return Enums.stateColor.transparentHover
                return Enums.stateColor.controlBgTransparent
            case Enums.button.style_filled:
                var statusColor = Enums.statusLevel.getColorByLevel(level)
                if (!effectiveEnabled) {
                    // Preserve the level hue while disabled instead of using neutral gray. 禁用态保留 level 色相（淡化版），不退回中性灰背景。
                    // Otherwise an error-filled destructive button becomes indistinguishable from a default button. 否则错误填充的危险按钮会与默认按钮无法区分。
                    return Qt.rgba(
                        statusColor.r,
                        statusColor.g,
                        statusColor.b,
                        Enums.stateColor.filledDisabledAlpha
                    )
                }
                if ((Enums.isVintageTicket || Enums.isNeumorphism) && pressed)
                    return Qt.darker(statusColor, 1.12)
                if ((Enums.isVintageTicket || Enums.isNeumorphism) && hovered)
                    return Qt.lighter(statusColor, 1.12)
                if (pressed) return Enums.stateColor.filledPressed
                if (hovered) return Enums.stateColor.filledHover
                return statusColor
            case Enums.button.style_gradient:
                if (!effectiveEnabled) return Enums.isVintageTicket
                    ? Enums.stateColor.disabledBg : Enums.stateColor.disabled
                if (pressed) return Qt.darker(Enums.accentColor, 1.1)
                if (hovered) return Qt.lighter(Enums.accentColor, 1.1)
                return Enums.accentColor
            default:
                return _getDefaultBgColor()
        }
    }

    // Border color 边框色
    readonly property color borderColor: {
        if (!Enums.stateColor) return Enums.stateColor.border

        if (Enums.isNeobrutalism) return _neoBorderColor()
        if (Enums.isVintageTicket) return _ticketBorderColor()

        if (isToggleChecked && style === Enums.button.style_primary) {
            return Enums.accentColor
        }
        
        switch (style) {
            case Enums.button.style_text:
            case Enums.button.style_hyperlink:
            case Enums.button.style_primary:
            case Enums.button.style_gradient:
                return Enums.transparent
            case Enums.button.style_filled:
                if (!effectiveEnabled) return Enums.stateColor.divider
                return Enums.statusLevel.getColorByLevel(level)
            default:
                if (!effectiveEnabled) return Enums.stateColor.border
                return Enums.stateColor.borderStrong
        }
    }

    // Text color 文字色
    readonly property color textColor: {
        if (!Enums.textColor) return Enums.textColor.primary

        if (Enums.isNeobrutalism) return _neoTextColor()

        if (isToggleChecked) {
            if (style === Enums.button.style_primary) {
                if (!effectiveEnabled) return Enums.textColor.disabled
                return Enums.accentColor
            }
            if (!effectiveEnabled) return Enums.textColor.tertiary
            if (pressed) return Enums.textColor.strong
            return Enums.accentForeground
        }
        
        switch (style) {
            case Enums.button.style_primary:
            case Enums.button.style_gradient:
            case Enums.button.style_filled:
                if (!effectiveEnabled) return Enums.textColor.tertiary
                return Enums.accentForeground
            case Enums.button.style_hyperlink:
                if (!effectiveEnabled) return Enums.textColor.disabled
                if (pressed) return Qt.darker(Enums.accentColor, 1.2)
                if (hovered) return Qt.lighter(Enums.accentColor, 1.1)
                return Enums.accentColor
            case Enums.button.style_text:
                var sc = Enums.statusLevel.getColorByLevel(level)
                if (!effectiveEnabled) return Enums.textColor.disabled
                if (pressed) return Qt.darker(sc, 1.2)
                if (hovered) return Qt.lighter(sc, 1.1)
                return sc
            default:
                if (!effectiveEnabled) return Enums.textColor.disabled
                if (pressed) return Enums.textColor.tertiary
                return Enums.textColor.primary
        }
    }

    // ==================== Internal Methods 内部方法 ====================
    function _getDefaultBgColor() {
        if (!effectiveEnabled) return Enums.stateColor.controlBgDisabled
        if (pressed) return Enums.stateColor.controlBgPressed
        if (hovered) return Enums.stateColor.controlBgHover
        return Enums.stateColor.controlBg
    }

    // Neobrutalism color helpers 新粗野主义配色辅助
    // Color tokens already adapt under the neo skin. 颜色 token 已在 neo 皮肤下自动适配。
    // Only structural differences remain: primary and filled buttons use a black border in neo while Fluent uses transparent. 此处仅保留结构差异：neo 下 primary 和 filled 按钮使用黑色边框，而 Fluent 使用透明边框。
    // Other text uses shared tokens, while accent styles require a light foreground. 其他文本使用共享 token，而 accent 类样式需要浅色前景。
    function _neoIsAccentStyle() {
        return style === Enums.button.style_primary ||
               style === Enums.button.style_filled ||
               style === Enums.button.style_gradient
    }
    function _neoBorderColor() {
        // Neo uses a solid black border for non-transparent styles; transparent, text, and hyperlink styles have none. neo 对非透明样式使用纯黑边框；透明、文本和超链接样式不使用边框。
        if (style === Enums.button.style_transparent ||
            style === Enums.button.style_text ||
            style === Enums.button.style_hyperlink) {
            return Enums.transparent
        }
        return Enums.neo.borderColor
    }
    function _ticketBorderColor() {
        if (style === Enums.button.style_transparent ||
            style === Enums.button.style_text ||
            style === Enums.button.style_hyperlink) {
            return Enums.transparent
        }
        return Enums.ticket.borderColor
    }
    function _neoTextColor() {
        if (_neoIsAccentStyle()) {
            if (!effectiveEnabled) {
                return Qt.rgba(
                    Enums.neo.primaryForeground.r,
                    Enums.neo.primaryForeground.g,
                    Enums.neo.primaryForeground.b,
                    Enums.opacityLevel.heavy
                )
            }
            return Enums.neo.primaryForeground
        }
        if (style === Enums.button.style_hyperlink) {
            return Enums.neo.primary
        }
        if (!effectiveEnabled) return Enums.neo.secondaryForeground
        return Enums.neo.foreground
    }
}
