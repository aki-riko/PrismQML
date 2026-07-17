// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ComboBoxStyleHelper - Style calculation helper for ComboBox ComboBox样式计算辅助
// Extracted from ComboBoxCore for modularity 从ComboBoxCore提取以模块化
QtObject {
    id: styleHelper
    
    // ==================== Required Props 必需属性 ====================
    required property var control  // Parent ComboBox control 父ComboBox控件
    
    // ==================== Internal Methods 内部方法 ====================
    // Unified with Button controlBg series 与Button统一使用controlBg系列
    function getBackgroundColor() {
        if (!Enums || !Enums.stateColor) return Enums.transparent
        
        var c = control
        
        // Primary style 主样式
        if (c.style === Enums.comboBox.style_primary) {
            if (!c.enabled) return Enums.stateColor.disabledBg
            if (c.popupVisible) return Qt.darker(c.accentColor, Enums.comboBox.primaryPopupDarken)
            if (c.pressed) return Qt.darker(c.accentColor, Enums.comboBox.primaryPressedDarken)
            if (c.hovered) return Qt.lighter(c.accentColor, Enums.comboBox.primaryHoverLighten)
            return c.accentColor
        }
        
        // Transparent style 透明样式
        // Use controlBgTransparent (same RGB as hover, alpha=0) to prevent gray flash during ColorAnimation 使用 controlBgTransparent 防止颜色动画灰色闪烁

        if (c.style === Enums.comboBox.style_transparent) {
            if (!c.enabled) return Enums.stateColor.controlBgTransparent
            if (c.popupVisible) return Enums.stateColor.transparentPressed
            if (c.pressed) return Enums.stateColor.transparentPressed
            if (c.hovered) return Enums.stateColor.transparentHover
            return Enums.stateColor.controlBgTransparent
        }
        
        // Default style uses controlBg, same as Button 默认样式使用与 Button 相同的 controlBg

        if (!c.enabled) return Enums.stateColor.controlBgDisabled
        if (c.popupVisible) return Enums.stateColor.controlBgPressed
        if (c.pressed) return Enums.stateColor.controlBgPressed
        if (c.hovered) return Enums.stateColor.controlBgHover
        return Enums.stateColor.controlBg
    }
    
    // Text color 文本色
    function getTextColor() {
        if (!control.enabled) return Enums.textColor.disabled
        if (control.style === Enums.comboBox.style_primary) return Enums.accentForeground
        if (control.currentText === "") return Enums.textColor.disabled
        return Enums.textColor.primary
    }
    
    // Border color 边框色
    // Use unified border color 使用统一边框色
    function getBorderColor() {
        return Enums.stateColor.borderStrong
    }
}
