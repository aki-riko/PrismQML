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

    // ==================== Public Props 公开属性 ====================
    property int checkState: Enums.toggle.state_unchecked
    property bool hovered: false
    property bool pressed: false
    property color checkedColor: Enums.accentColor

    // ==================== Readonly State 只读状态 ====================
    readonly property int _indicatorRadius: Enums.isNeobrutalism ? Enums.neo.radius
                                                                 : (Enums.radius.small)
    readonly property bool _hasCheckState: checkState !== Enums.toggle.state_unchecked
    readonly property int _indicatorBorderWidth: {
        if (Enums.isNeobrutalism) return Enums.neo.borderWidth
        return _hasCheckState ? Enums.border.none : Enums.border.medium
    }
    readonly property color _indicatorColor: {
        if (!enabled) {
            if (_hasCheckState) return Enums.stateColor.disabledBorder
            if (Enums.isNeobrutalism) return Enums.stateColor.checkBoxFill
            return Enums.transparent
        }
        if (_hasCheckState) {
            if (pressed) return Qt.darker(checkedColor, 1.15)
            if (hovered) return Qt.lighter(checkedColor, 1.08)
            return checkedColor
        }
        if (pressed) return Enums.stateColor.checkBoxFillPressed
        if (hovered) return Enums.stateColor.checkBoxFillHover
        return Enums.stateColor.checkBoxFill
    }
    readonly property color _indicatorBorderColor: {
        if (Enums.isNeobrutalism && _hasCheckState) return enabled ? Enums.stateColor.toggleBorder : Enums.stateColor.disabledBorder
        if (_hasCheckState) return Enums.transparent
        if (!enabled) return Enums.stateColor.disabledBorder
        if (pressed) return Enums.stateColor.togglePressed
        if (hovered) return Enums.stateColor.toggleBorderHover
        return Enums.stateColor.toggleBorder
    }
    readonly property color _checkIconColor: {
        if (!enabled) return Enums.textColor.disabled
        return Enums.isDark && !Enums.isNeobrutalism ? Enums.themeColors.foregroundLight : Enums.accentForeground
    }

    // ==================== Size 尺寸 ====================
    width: Enums.controlSize.checkboxOuter
    height: Enums.controlSize.checkboxOuter
    radius: _indicatorRadius

    // Calculated colors 计算颜色
    // Checked uses accent; unchecked uses skin fill 选中使用强调色，未选使用皮肤填充。
    color: _indicatorColor

    // Neo keeps a visible outline. Neo 保持可见描边。
    border.width: _indicatorBorderWidth
    border.color: _indicatorBorderColor

    Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
    Behavior on border.color { ColorAnimation { duration: Enums.duration.fast } }

    // ==================== Content 内容 ====================
    CheckIcon {
        anchors.centerIn: parent
        width: Enums.controlSize.checkboxInner
        height: Enums.controlSize.checkboxInner
        state: indicator.checkState
        color: indicator._checkIconColor
        visible: indicator._hasCheckState
        scale: indicator._hasCheckState ? 1 : 0
        Behavior on scale {
            NumberAnimation {
                duration: Enums.duration.fast
                easing.type: Easing.OutBack
            }
        }
    }
}
