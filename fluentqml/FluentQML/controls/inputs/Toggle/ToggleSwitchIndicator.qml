// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// ToggleSwitchIndicator - ToggleSwitch indicator 开关指示器
// Internal module for Toggle Toggle内部模块
Rectangle {
    id: track

    // ==================== Props 属性 ====================
    property bool checked: false
    property color checkedColor: Enums.accentColor

    // ==================== Signals 信号 ====================
    signal clicked()

    // ==================== Size 尺寸 ====================
    width: Enums.controlSize.switchWidth
    height: Enums.controlSize.switchHeight
    radius: height / 2

    // ==================== Color 颜色 ====================
    // enabled-unchecked: 浅灰 #c0c0c0 / #4d4d4d  (低对比, 不喧宾夺主)
    // enabled-checked:   accent 实色
    // disabled-unchecked: 深灰 (实色饱满) + opacity 0.65 → 看起来"灰扑扑且暗淡"
    // disabled-checked:   accent + opacity 0.65 → 淡 accent
    color: {
        // 选中=checkedColor(=accentColor, neo 下自动橙); neo 未选要白轨道(Fluent 为灰, 结构差异)
        if (Enums.isNeobrutalism) {
            if (!enabled) return checked ? Qt.rgba(0.98,0.45,0.09,0.5) : Enums.stateColor.checkBoxFill
            return checked ? checkedColor : Enums.stateColor.checkBoxFill
        }
        if (!enabled) {
            if (checked) return checkedColor
            return Enums.isDark ? Qt.rgba(1,1,1,0.4) : Qt.rgba(0,0,0,0.4)
        }
        return checked ? checkedColor : (Enums.isDark ? "#4d4d4d" : "#c0c0c0")
    }
    opacity: enabled ? 1.0 : 0.65
    // neo 结构差异: Fluent 开关无边, neo 轨道+滑块加黑边显形
    border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : 0
    border.color: Enums.isNeobrutalism ? Enums.stateColor.toggleBorder : Enums.transparent

    Behavior on color { ColorAnimation { duration: Enums.duration.normal } }
    Behavior on opacity { NumberAnimation { duration: Enums.duration.normal } }

    // ==================== Handle 滑块 ====================
    Rectangle {
        id: handle
        width: Enums.controlSize.switchThumb
        height: Enums.controlSize.switchThumb
        radius: width / 2
        color: enabled ? "white" : Enums.gray.background
        // neo: 滑块黑边显形(白轨道上白滑块否则看不见)
        border.width: Enums.isNeobrutalism ? Enums.border.medium : 0
        border.color: Enums.isNeobrutalism ? Enums.stateColor.toggleBorder : Enums.transparent
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
        anchors.fill: parent
        enabled: track.enabled
        onClicked: track.clicked()
    }
}
