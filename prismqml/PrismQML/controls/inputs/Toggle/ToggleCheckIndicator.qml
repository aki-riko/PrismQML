// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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
    // 选中色=checkedColor(=accentColor, neo 下自动橙); 未选=checkBoxFill(neo 下自动白面)。颜色无需 neo 分支。
    color: {
        if (!enabled) {
            if (checkState > 0) return Enums.stateColor.disabledBorder
            return Enums.isNeobrutalism ? Enums.stateColor.checkBoxFill : Enums.transparent
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

    // neo 结构差异: 黑粗边始终在(含选中态强调描边); Fluent: 选中无边
    border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth
                  : (checkState > 0 ? 0 : Enums.border.medium)
    border.color: {
        // neo 选中态也要黑边(结构差异, Fluent 选中返回 transparent); 非选中黑边由 token 自动返回
        if (Enums.isNeobrutalism && checkState > 0) return enabled ? Enums.stateColor.toggleBorder : Qt.rgba(0,0,0,0.4)
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
        // 勾色: neo(light)→白; Fluent 随明暗(neo 下 isDark=false 同样取白)
        color: Enums.isDark && !Enums.isNeobrutalism ? "black" : "white"
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
