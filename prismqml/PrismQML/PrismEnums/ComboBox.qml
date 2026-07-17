// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ComboBox - ComboBox type enums 下拉框类型枚举
QtObject {
    // Type 类型
    readonly property int type_default: 0
    readonly property int type_multi: 1
    readonly property int type_tree: 2
    readonly property int type_multi_tree: 3
    readonly property int type_font: 4
    // Style 样式
    readonly property int style_default: 0
    readonly property int style_primary: 1
    readonly property int style_transparent: 2
    // Primary style color factors 主样式颜色系数
    readonly property real primaryPopupDarken: 1.1
    readonly property real primaryPressedDarken: 1.15
    readonly property real primaryHoverLighten: 1.08
    // Feature 功能
    readonly property int feature_none: 0
    readonly property int feature_editable: 1
}
