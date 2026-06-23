// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// ToggleRadioIndicator - RadioButton indicator 单选按钮指示器
// Internal module for Toggle Toggle内部模块
Rectangle {
    id: indicator

    // ==================== Props 属性 ====================
    property bool checked: false
    property bool hovered: false
    property bool pressed: false

    // ==================== Size 尺寸 ====================
    width: Enums.controlSize.radioOuter
    height: Enums.controlSize.radioOuter
    radius: width / 2

    // ==================== Color Calc 颜色计算 ====================
    // 选中=accentColor(neo 下自动橙); 未选 neo 下要白面显形(Fluent 为透明, 此为结构差异)
    readonly property color _indicatorColor: {
        if (!enabled) return checked ? Enums.stateColor.disabledBorder
                       : (Enums.isNeobrutalism ? Enums.stateColor.checkBoxFill : Enums.transparent)
        if (checked) {
            if (pressed) return Qt.darker(Enums.accentColor, 1.15)
            if (hovered) return Qt.lighter(Enums.accentColor, 1.08)
            return Enums.accentColor
        }
        return Enums.isNeobrutalism ? Enums.stateColor.checkBoxFill : Enums.transparent
    }

    // 边框: neo 黑边由 token(toggleBorder)自动返回; Fluent 暗色用 tertiary
    readonly property color _borderColor: {
        if (!enabled) return Enums.stateColor.disabledBorder
        if (Enums.isNeobrutalism) return Enums.stateColor.toggleBorder
        if (pressed) return Enums.stateColor.togglePressed
        if (hovered) return Enums.stateColor.toggleBorderHover
        return Enums.isDark ? Enums.textColor.tertiary : Enums.stateColor.toggleBorder
    }

    color: _indicatorColor
    // neo 结构差异: 选中态也有黑粗边; Fluent: 选中无边
    border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : (checked ? 0 : Enums.border.medium)
    border.color: _borderColor

    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
    Behavior on border.color { ColorAnimation { duration: Enums.duration.fast } }

    // ==================== Inner Dot 内部圆点 ====================
    Rectangle {
        anchors.centerIn: parent
        width: Enums.controlSize.radioInner
        height: Enums.controlSize.radioInner
        radius: width / 2
        color: Enums.accentForeground  // neo 下 token 自动返回白
        visible: indicator.checked
        scale: indicator.checked ? 1 : 0
        Behavior on scale {
            NumberAnimation {
                duration: Enums.duration.fast
                easing.type: Easing.OutBack
            }
        }
    }
}
