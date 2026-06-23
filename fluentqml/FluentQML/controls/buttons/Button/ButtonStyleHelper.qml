// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// ButtonStyleHelper - Button color calculation 按钮颜色计算
// Extracts complex color logic from ButtonCore 从ButtonCore提取复杂颜色逻辑
QtObject {
    id: helper
    
    // ==================== Required Props 必需属性 ====================
    required property int style
    required property int feature
    required property int level
    required property bool controlEnabled
    required property bool loading
    required property bool countdownActive
    required property bool hovered
    required property bool pressed
    required property bool isToggleChecked

    // ==================== Computed Props 计算属性 ====================
    readonly property bool effectiveEnabled: controlEnabled && !loading && !countdownActive
    
    // ==================== Background Color 背景色 ====================
    readonly property color bgColor: {
        if (!Enums || !Enums.stateColor) return Enums.stateColor.controlBg

        if (isToggleChecked) {
            if (style === Enums.button.style_primary) {
                if (!effectiveEnabled) return Enums.stateColor.disabled
                if (pressed) return Enums.stateColor.controlBgPressed
                if (hovered) return Enums.stateColor.controlBgHover
                return Enums.cardColor
            }
            if (!effectiveEnabled) return Enums.stateColor.disabled
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
                if (!effectiveEnabled) {
                    // 禁用态保留 level 色相 (淡化版), 不退回中性灰背景 — 否则 destructive
                    // 按钮 (error filled) 灰化后失去"危险"提示, 跟旁边 default 按钮分不开。
                    var fc = Enums.statusLevel.getColorByLevel(level)
                    return Qt.rgba(fc.r, fc.g, fc.b, 0.45)
                }
                if (pressed) return Enums.stateColor.filledPressed
                if (hovered) return Enums.stateColor.filledHover
                return Enums.statusLevel.getColorByLevel(level)
            case Enums.button.style_gradient:
                if (!effectiveEnabled) return Enums.stateColor.disabled
                if (pressed) return Qt.darker(Enums.accentColor, 1.1)
                if (hovered) return Qt.lighter(Enums.accentColor, 1.1)
                return Enums.accentColor
            default:
                return _getDefaultBgColor()
        }
    }
    
    function _getDefaultBgColor() {
        if (!effectiveEnabled) return Enums.stateColor.controlBgDisabled
        if (pressed) return Enums.stateColor.controlBgPressed
        if (hovered) return Enums.stateColor.controlBgHover
        return Enums.stateColor.controlBg
    }

    // ==================== Neobrutalism 配色函数 ====================
    // 颜色值已由 token 层(accentColor/stateColor/statusLevel)在 neo 下自动返回;
    // 此处仅保留【结构差异】: neo 下 primary/filled 按钮也要黑边(Fluent 逻辑返回透明),
    // 以及文本色统一(token textColor 近黑够用, 但 accent 类需白字)。
    function _neoIsAccentStyle() {
        return style === Enums.button.style_primary ||
               style === Enums.button.style_filled ||
               style === Enums.button.style_gradient
    }
    function _neoBorderColor() {
        // neo: 非透明类一律纯黑粗边; 透明/文本/超链接无边
        if (style === Enums.button.style_transparent ||
            style === Enums.button.style_text ||
            style === Enums.button.style_hyperlink) {
            return Enums.transparent
        }
        return Enums.neo.borderColor
    }
    function _neoTextColor() {
        if (_neoIsAccentStyle()) {
            if (!effectiveEnabled) return Qt.rgba(1, 1, 1, 0.7)
            return Enums.neo.primaryForeground
        }
        if (style === Enums.button.style_hyperlink) {
            return Enums.neo.primary
        }
        if (!effectiveEnabled) return Enums.neo.secondaryForeground
        return Enums.neo.foreground
    }
    
    // ==================== Border Color 边框色 ====================
    readonly property color borderColor: {
        if (!Enums.stateColor) return Enums.stateColor.border

        if (Enums.isNeobrutalism) return _neoBorderColor()

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
    
    // ==================== Text Color 文字色 ====================
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
}
