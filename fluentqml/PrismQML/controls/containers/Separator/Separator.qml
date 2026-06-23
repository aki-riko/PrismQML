// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../.."
import ".."

// Separator - Unified separator component 统一分隔线组件
// Usage: Separator { type: Enums.separator.horizontal }
Widget {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int type: 0  // 0=horizontal, 1=vertical
    property real lineWidth: Enums.border.thin
    property real lineLength: 0  // 0=auto fill, >0=fixed length  0=自动填充，>0=固定长度
    property color lineColor: Enums.stateColor.divider  // 线条颜色,默认 divider, 可覆盖

    // ==================== Internal 内部状态 ====================
    readonly property bool isHorizontal: type === 0
    readonly property bool autoFill: lineLength <= 0

    // ==================== Size 尺寸 ====================
    // 水平分隔线：宽度填充或固定，高度为线宽
    // 垂直分隔线：宽度为线宽，高度填充或固定
    contentWidth: isHorizontal ? (autoFill ? 100 : lineLength) : lineWidth
    contentHeight: isHorizontal ? lineWidth : (autoFill ? 100 : lineLength)

    // Layout fill support 布局填充支持（仅autoFill时生效）
    Layout.fillWidth: isHorizontal && autoFill
    Layout.fillHeight: !isHorizontal && autoFill
    Layout.preferredHeight: isHorizontal ? lineWidth : (autoFill ? -1 : lineLength)
    Layout.preferredWidth: isHorizontal ? (autoFill ? -1 : lineLength) : lineWidth

    // ==================== Visual 视觉 ====================
    Rectangle {
        anchors.fill: parent
        color: control.lineColor
    }

}
