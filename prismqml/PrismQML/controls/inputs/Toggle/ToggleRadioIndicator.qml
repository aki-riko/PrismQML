// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// ToggleRadioIndicator - RadioButton indicator 单选按钮指示器
// Internal module for Toggle Toggle内部模块
Rectangle {
    id: indicator

    // ==================== Public Props 公开属性 ====================
    property bool checked: false
    property bool hovered: false
    property bool pressed: false

    // ==================== Readonly State 只读状态 ====================
    readonly property int _indicatorBorderWidth: {
        if (Enums.hasOutlinedSurfaces) return Enums.surfaceBorderWidth(Enums.border.thin)
        return checked ? Enums.border.none : Enums.border.medium
    }
    readonly property color _innerDotColor: {
        if (!enabled) return Enums.textColor.disabled
        return Enums.accentForeground
    }
    // Checked uses accent; Prism/neo unchecked keeps fill for visibility 选中使用强调色，Prism/neo 未选保留填充。
    readonly property color _indicatorColor: {
        if (!enabled) return checked ? Enums.stateColor.disabledBorder
                       : (Enums.hasOutlinedSurfaces ? Enums.stateColor.checkBoxFill : Enums.transparent)
        if (checked) {
            if (pressed) return Qt.darker(Enums.accentColor, 1.15)
            if (hovered) return Qt.lighter(Enums.accentColor, 1.08)
            return Enums.accentColor
        }
        if (Enums.hasOutlinedSurfaces) {
            if (pressed) return Enums.stateColor.checkBoxFillPressed
            if (hovered) return Enums.stateColor.checkBoxFillHover
            return Enums.stateColor.checkBoxFill
        }
        return Enums.transparent
    }

    // Border follows skin token 边框跟随皮肤 token。
    readonly property color _borderColor: {
        if (!enabled) return Enums.stateColor.disabledBorder
        if (Enums.hasOutlinedSurfaces) return Enums.stateColor.toggleBorder
        if (pressed) return Enums.stateColor.togglePressed
        if (hovered) return Enums.stateColor.toggleBorderHover
        return Enums.isDark ? Enums.textColor.tertiary : Enums.stateColor.toggleBorder
    }

    // ==================== Size 尺寸 ====================
    width: Enums.controlSize.radioOuter
    height: Enums.controlSize.radioOuter
    radius: width / 2

    // Calculated visual style 计算后的视觉样式
    color: _indicatorColor
    // Neo/Prism keep a visible outline even when checked Neo/Prism 选中也保留轮廓。
    border.width: _indicatorBorderWidth
    border.color: _borderColor

    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
    Behavior on border.color { ColorAnimation { duration: Enums.duration.fast } }

    // ==================== Content 内容 ====================
    Rectangle {
        anchors.centerIn: parent
        width: Enums.controlSize.radioInner
        height: Enums.controlSize.radioInner
        radius: width / 2
        color: indicator._innerDotColor
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
