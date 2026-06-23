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
    readonly property color _indicatorColor: {
        if (Enums.isNeobrutalism) {
            // neo: 选中橙底, 未选白底(靠黑粗边显形)
            if (!enabled) return checked ? Qt.rgba(0,0,0,0.2) : Enums.neo.muted
            if (checked) {
                if (pressed) return Qt.darker(Enums.neo.primary, 1.15)
                if (hovered) return Qt.lighter(Enums.neo.primary, 1.08)
                return Enums.neo.primary
            }
            return Enums.neo.surface
        }
        if (!enabled) return checked ? Enums.stateColor.disabledBorder : Enums.transparent
        if (checked) {
            if (pressed) return Qt.darker(Enums.accentColor, 1.15)
            if (hovered) return Qt.lighter(Enums.accentColor, 1.08)
            return Enums.accentColor
        }
        return Enums.transparent
    }

    readonly property color _borderColor: {
        if (Enums.isNeobrutalism) return enabled ? Enums.neo.borderColor : Qt.rgba(0,0,0,0.4)
        if (!enabled) return Enums.stateColor.disabledBorder
        if (pressed) return Enums.stateColor.togglePressed
        if (hovered) return Enums.stateColor.toggleBorderHover
        return Enums.isDark ? Enums.textColor.tertiary : Enums.stateColor.toggleBorder
    }

    color: _indicatorColor
    // neo: 黑粗边始终在; Fluent: 选中无边
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
        color: Enums.isNeobrutalism ? "white" : Enums.accentForeground
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
