// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// SegmentedSelectedBackground - Sliding selected-cell background 滑动选中背景
// Owns the two-axis geometry so the control entry stays within its budget.
// 自持双轴几何，使控件入口保持在行数预算内。
Rectangle {
    id: selectedBg

    // ==================== Required Props 必需属性 ====================
    required property var host

    // ==================== Internal Props 内部属性 ====================
    readonly property bool vertical: host.orientation === Qt.Vertical

    // ==================== Size 尺寸 ====================
    x: host._slideX
    y: selectedBg.vertical ? host._slideY : Enums.spacing.xxs
    width: host._selectedItemWidth
    height: selectedBg.vertical
        ? host._selectedItemHeight
        : host.height - Enums.spacing.xxs * 2
    radius: Enums.surfaceRadius(Enums.radius.small)
    visible: host._safeItems.length > 0
    color: Enums.stateColor.segmentedSelected
    border.width: Enums.surfaceBorderWidth(Enums.border.thin)
    border.color: Enums.stateColor.segmentedSelectedBorder

    // Geometry transitions; the cross-axis pair only animates in vertical mode so
    // the horizontal treatment keeps its original instant geometry.
    // 几何过渡; 副轴两个动画只在纵向模式生效, 横向保持原有的即时几何。
    Behavior on x { NumberAnimation { duration: Enums.duration.normal; easing.type: Easing.OutCubic } }
    Behavior on width { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
    Behavior on y {
        enabled: selectedBg.vertical
        NumberAnimation { duration: Enums.duration.normal; easing.type: Easing.OutCubic }
    }
    Behavior on height {
        enabled: selectedBg.vertical
        NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic }
    }
}
