// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"

// ToggleCheckIndicator - CheckBox indicator 复选框指示器
// Internal module for Toggle Toggle内部模块
Rectangle {
    id: indicator

    // ==================== Props 属性 ====================
    property int checkState: 0  // 0=Unchecked, 1=Partial, 2=Checked
    property bool hovered: false
    property bool pressed: false
    property color checkedColor: Enums.accentColor

    // ==================== Size 尺寸 ====================
    width: Enums.controlSize.checkboxOuter
    height: Enums.controlSize.checkboxOuter
    radius: Enums.isNeobrutalism ? Enums.neo.radius : Enums.radius.small

    // ==================== Color Calc 颜色计算 ====================
    color: {
        if (Enums.isNeobrutalism) {
            // neo: 选中橙底, 未选白底; hover/press 用变暗变亮
            if (!enabled) return checkState > 0 ? Qt.rgba(0,0,0,0.2) : Enums.neo.muted
            if (checkState > 0) {
                if (pressed) return Qt.darker(Enums.neo.primary, 1.15)
                if (hovered) return Qt.lighter(Enums.neo.primary, 1.08)
                return Enums.neo.primary
            }
            return Enums.neo.surface
        }
        if (!enabled) {
            if (checkState > 0) return Enums.stateColor.disabledBorder
            return Enums.transparent
        }
        if (checkState > 0) {
            if (pressed) return Qt.darker(checkedColor, 1.15)
            if (hovered) return Qt.lighter(checkedColor, 1.08)
            return checkedColor
        }
        if (pressed) return Enums.stateColor.checkBoxFillPressed
        if (hovered) return Enums.stateColor.checkBoxFillHover
        return Enums.stateColor.checkBoxFill
    }

    // neo: 黑粗边始终在(包括选中态, 强调描边); Fluent: 选中无边
    border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth
                  : (checkState > 0 ? 0 : Enums.border.medium)
    border.color: {
        if (Enums.isNeobrutalism) return enabled ? Enums.neo.borderColor : Qt.rgba(0,0,0,0.4)
        if (checkState > 0) return Enums.transparent
        if (!enabled) return Enums.stateColor.disabledBorder
        if (pressed) return Enums.stateColor.togglePressed
        if (hovered) return Enums.stateColor.toggleBorderHover
        return Enums.stateColor.toggleBorder
    }

    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
    Behavior on border.color { ColorAnimation { duration: Enums.duration.fast } }

    // ==================== Check Icon 勾选图标 ====================
    CheckIcon {
        anchors.centerIn: parent
        width: Enums.controlSize.checkboxInner
        height: Enums.controlSize.checkboxInner
        state: indicator.checkState
        // neo: 橙底白勾; Fluent: 随明暗
        color: Enums.isNeobrutalism ? "white" : (Enums.isDark ? "black" : "white")
        visible: indicator.checkState > 0
        scale: indicator.checkState > 0 ? 1 : 0
        Behavior on scale {
            NumberAnimation {
                duration: Enums.duration.fast
                easing.type: Easing.OutBack
            }
        }
    }
}
