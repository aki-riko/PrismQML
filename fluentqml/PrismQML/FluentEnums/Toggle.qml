// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Toggle - Unified toggle control enums 统一切换控件枚举
// For CheckBox/RadioButton/ToggleSwitch 用于复选框/单选按钮/开关
QtObject {
    // ==================== Control Type 控件类型 ====================
    readonly property int control_checkbox: 0   // CheckBox 复选框
    readonly property int control_radio: 1      // RadioButton 单选按钮
    readonly property int control_switch: 2     // ToggleSwitch 开关

    // ==================== Display Type 显示类型 ====================
    readonly property int type_default: 0       // Default with text 默认带文字
    readonly property int type_indicator: 1     // Indicator only 仅指示器
    readonly property int type_subtitle: 2      // With subtitle 带副标题
}
