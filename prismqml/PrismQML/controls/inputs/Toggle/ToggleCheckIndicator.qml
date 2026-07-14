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
    readonly property int _indicatorRadius: Enums.isNeobrutalism ? Enums.neo.radius
                                                                 : (Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small)
    readonly property int _indicatorBorderWidth: {
        if (Enums.isNeobrutalism) return Enums.neo.borderWidth
        if (Enums.isPrismDesign) return Enums.prismDesign.borderWidth
        return checkState > 0 ? Enums.border.none : Enums.border.medium
    }
    readonly property color _indicatorColor: {
        if (!enabled) {
            if (checkState > 0) return Enums.isPrismDesign ? Enums.stateColor.primaryDisabled : Enums.stateColor.disabledBorder
            if (Enums.isNeobrutalism) return Enums.stateColor.checkBoxFill
            if (Enums.isPrismDesign) return Enums.stateColor.controlBgDisabled
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
    readonly property color _indicatorBorderColor: {
        if (Enums.isNeobrutalism && checkState > 0) return enabled ? Enums.stateColor.toggleBorder : Enums.stateColor.disabledBorder
        if (Enums.isPrismDesign && checkState > 0) return enabled ? Enums.accentColorDark : Enums.stateColor.disabledBorder
        if (checkState > 0) return Enums.transparent
        if (!enabled) return Enums.stateColor.disabledBorder
        if (pressed) return Enums.stateColor.togglePressed
        if (hovered) return Enums.stateColor.toggleBorderHover
        return Enums.stateColor.toggleBorder
    }
    readonly property color _checkIconColor: {
        if (!enabled) return Enums.textColor.disabled
        if (Enums.isPrismDesign) return Enums.accentForeground
        return Enums.isDark && !Enums.isNeobrutalism ? Enums.themeColors.foregroundLight : Enums.accentForeground
    }

    // ==================== Size 尺寸 ====================
    width: Enums.controlSize.checkboxOuter
    height: Enums.controlSize.checkboxOuter
    radius: _indicatorRadius

    // ==================== Color Calc 颜色计算 ====================
    // Checked uses accent; unchecked uses skin fill 选中使用强调色，未选使用皮肤填充。
    color: _indicatorColor

    // Neo and Prism keep a visible outline  Neo 与 Prism 保持可见描边。
    border.width: _indicatorBorderWidth
    border.color: _indicatorBorderColor

    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
    Behavior on border.color { ColorAnimation { duration: Enums.duration.fast } }

    // ==================== Check Icon 勾选图标 ====================
    CheckIcon {
        anchors.centerIn: parent
        width: Enums.controlSize.checkboxInner
        height: Enums.controlSize.checkboxInner
        state: indicator.checkState
        color: indicator._checkIconColor
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
