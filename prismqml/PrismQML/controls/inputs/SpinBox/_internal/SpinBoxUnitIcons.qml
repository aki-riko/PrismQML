// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// SpinBoxUnitIcons - Optional icon units beside the spin value 微调框数值两侧的可选图标单位
// Owns unit icon measurement and placement; SpinBoxCore only wires the properties.
// 负责图标单位的度量与定位，SpinBoxCore 只负责属性接线。
Item {
    id: unitIcons

    // ==================== Required Props 必需属性 ====================
    required property var spinControl
    required property var textInputItem

    // ==================== Readonly State 只读状态 ====================
    // Displayed value width, never wider than the text field 显示数值宽度,不超过文本框宽度
    readonly property real valueWidth: Math.min(valueMetrics.width, textInputItem.width)
    // Left edge of the centered value text 居中数值文本的左边缘
    readonly property real valueLeft: textInputItem.x + (textInputItem.width - valueWidth) / 2
    readonly property real valueRight: valueLeft + valueWidth
    // Text field bounds keep unit icons inside the input area 文本框边界保证图标单位留在输入区内
    readonly property real iconMinX: textInputItem.x
    readonly property real iconMaxX: textInputItem.x + textInputItem.width

    // ==================== Size 尺寸 ====================
    anchors.fill: parent

    // ==================== Content 内容 ====================
    TextMetrics {
        id: valueMetrics
        font: unitIcons.textInputItem.font
        text: unitIcons.spinControl.displayValue
    }

    // Leading unit icon 前置图标单位
    Icon {
        id: prefixIcon
        objectName: "spinBoxPrefixIcon"
        x: Math.max(unitIcons.iconMinX, unitIcons.valueLeft - width - Enums.spacing.xs)
        anchors.verticalCenter: parent.verticalCenter
        visible: unitIcons.spinControl.prefixIcon !== ""
        icon: unitIcons.spinControl.prefixIcon
        iconSize: unitIcons.spinControl.iconSize
        color: unitIcons.spinControl.inputTextColor
        themeAware: unitIcons.spinControl.iconThemeAware
    }

    // Trailing unit icon 后置图标单位
    Icon {
        id: suffixIcon
        objectName: "spinBoxSuffixIcon"
        x: Math.min(unitIcons.iconMaxX - width, unitIcons.valueRight + Enums.spacing.xs)
        anchors.verticalCenter: parent.verticalCenter
        visible: unitIcons.spinControl.suffixIcon !== ""
        icon: unitIcons.spinControl.suffixIcon
        iconSize: unitIcons.spinControl.iconSize
        color: unitIcons.spinControl.inputTextColor
        themeAware: unitIcons.spinControl.iconThemeAware
    }
}
