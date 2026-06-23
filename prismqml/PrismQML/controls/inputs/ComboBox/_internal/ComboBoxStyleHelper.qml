// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."

// ComboBoxStyleHelper - Style calculation helper for ComboBox ComboBox样式计算辅助
// Extracted from ComboBoxCore for modularity 从ComboBoxCore提取以模块化
QtObject {
    id: styleHelper
    
    // ==================== Required Props 必需属性 ====================
    required property var control  // Parent ComboBox control 父ComboBox控件
    
    // ==================== Background Color 背景色 ====================
    // Unified with Button controlBg series 与Button统一使用controlBg系列
    function getBackgroundColor() {
        if (!Enums || !Enums.stateColor) return Enums.transparent
        
        var c = control
        
        // Style 1: Filled style 填充样式
        if (c.style === 1) {
            if (!c.enabled) return Enums.stateColor.disabledBg
            if (c.popupVisible) return Qt.darker(c.accentColor, 1.1)
            if (c.pressed) return Qt.darker(c.accentColor, 1.15)
            if (c.hovered) return Qt.lighter(c.accentColor, 1.08)
            return c.accentColor
        }
        
        // Style 2: Transparent style 透明样式
        // Use controlBgTransparent (same RGB as hover, alpha=0) to prevent gray flash during ColorAnimation 使用 controlBgTransparent 防止颜色动画灰色闪烁

        if (c.style === 2) {
            if (!c.enabled) return Enums.stateColor.controlBgTransparent
            if (c.popupVisible) return Enums.stateColor.transparentPressed
            if (c.pressed) return Enums.stateColor.transparentPressed
            if (c.hovered) return Enums.stateColor.transparentHover
            return Enums.stateColor.controlBgTransparent
        }
        
        // Style 0: Default style - use controlBg (same as Button) 默认样式：使用 controlBg（与 Button 一致）

        if (!c.enabled) return Enums.stateColor.controlBgDisabled
        if (c.popupVisible) return Enums.stateColor.controlBgPressed
        if (c.pressed) return Enums.stateColor.controlBgPressed
        if (c.hovered) return Enums.stateColor.controlBgHover
        return Enums.stateColor.controlBg
    }
    
    // ==================== Text Color 文本色 ====================
    function getTextColor() {
        if (!control.enabled) return Enums.textColor.disabled
        if (control.style === 1) return Enums.accentForeground
        if (control.currentText === "") return Enums.textColor.disabled
        return Enums.textColor.primary
    }
    
    // ==================== Border Color 边框色 ====================
    // Use unified border color 使用统一边框色
    function getBorderColor() {
        return Enums.stateColor.borderStrong
    }
}
