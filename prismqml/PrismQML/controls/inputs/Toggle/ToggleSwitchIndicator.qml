// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// ToggleSwitchIndicator - ToggleSwitch indicator 开关指示器
// Internal module for Toggle Toggle内部模块
Rectangle {
    id: track

    // ==================== Props 属性 ====================
    property bool checked: false
    property bool hovered: false
    property bool pressed: false
    property color checkedColor: Enums.accentColor
    readonly property bool _effectiveHovered: hovered || switchArea.containsMouse
    readonly property bool _effectivePressed: pressed || switchArea.pressed
    readonly property color _trackColor: {
        if (Enums.isNeobrutalism) {
            if (!enabled) return checked ? Enums.stateColor.primaryDisabled : Enums.stateColor.checkBoxFill
            return checked ? checkedColor : Enums.stateColor.checkBoxFill
        }
        if (Enums.isPrismDesign) {
            if (!enabled) return checked ? Enums.stateColor.primaryDisabled : Enums.stateColor.controlBgDisabled
            if (checked) {
                if (_effectivePressed) return Qt.darker(checkedColor, 1.1)
                if (_effectiveHovered) return Qt.lighter(checkedColor, 1.06)
                return checkedColor
            }
            if (_effectivePressed) return Enums.stateColor.checkBoxFillPressed
            if (_effectiveHovered) return Enums.stateColor.checkBoxFillHover
            return Enums.stateColor.checkBoxFill
        }
        if (!enabled) {
            if (checked) return checkedColor
            return Enums.stateColor.disabledBorder
        }
        return checked ? checkedColor : Enums.stateColor.disabledBorder
    }
    readonly property real _trackOpacity: Enums.isPrismDesign ? 1.0 : (enabled ? 1.0 : 0.65)
    readonly property int _trackBorderWidth: Enums.isNeobrutalism ? Enums.neo.borderWidth
                                                                  : (Enums.isPrismDesign ? Enums.prismDesign.borderWidth : Enums.border.none)
    readonly property color _trackBorderColor: {
        if (Enums.isNeobrutalism) return Enums.stateColor.toggleBorder
        if (Enums.isPrismDesign) {
            if (!enabled) return Enums.stateColor.disabledBorder
            return checked ? Enums.accentColorDark : Enums.stateColor.toggleBorder
        }
        return Enums.transparent
    }
    readonly property color _handleColor: {
        if (Enums.isPrismDesign) {
            if (!enabled) return Enums.stateColor.controlBgDisabled
            return checked ? Enums.accentForeground : Enums.stateColor.controlBg
        }
        return enabled ? (Enums.isNeobrutalism ? Enums.neo.background : Enums.accentForeground) : Enums.gray.background
    }
    readonly property int _handleBorderWidth: Enums.isNeobrutalism ? Enums.border.medium
                                                                   : (Enums.isPrismDesign ? Enums.prismDesign.borderWidth : Enums.border.none)
    readonly property color _handleBorderColor: {
        if (Enums.isNeobrutalism) return Enums.stateColor.toggleBorder
        if (Enums.isPrismDesign) return enabled ? Enums.stateColor.border : Enums.stateColor.disabledBorder
        return Enums.transparent
    }

    // ==================== Signals 信号 ====================
    signal clicked()

    // ==================== Size 尺寸 ====================
    width: Enums.controlSize.switchWidth
    height: Enums.controlSize.switchHeight
    radius: height / 2

    // ==================== Color 颜色 ====================
    color: _trackColor
    opacity: _trackOpacity
    border.width: _trackBorderWidth
    border.color: _trackBorderColor

    Behavior on color { ColorAnimation { duration: Enums.duration.normal } }
    Behavior on opacity { NumberAnimation { duration: Enums.duration.normal } }

    // ==================== Handle 滑块 ====================
    Rectangle {
        id: handle
        width: Enums.controlSize.switchThumb
        height: Enums.controlSize.switchThumb
        radius: width / 2
        color: track._handleColor
        border.width: track._handleBorderWidth
        border.color: track._handleBorderColor
        anchors.verticalCenter: parent.verticalCenter
        x: checked ? parent.width - width - Enums.spacing.xxs : Enums.spacing.xxs

        Behavior on x {
            NumberAnimation {
                duration: Enums.duration.normal
                easing.type: Easing.OutCubic
            }
        }
    }

    // ==================== Interaction 交互 ====================
    MouseArea {
        id: switchArea
        anchors.fill: parent
        enabled: track.enabled
        hoverEnabled: true
        onClicked: track.clicked()
    }
}
