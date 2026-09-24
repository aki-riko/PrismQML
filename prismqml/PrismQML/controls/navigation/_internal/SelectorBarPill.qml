// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// SelectorBarPill - Sliding selected-cell background 滑动选中胶囊
// Owns its own geometry so the control entry stays within its line budget.
// 自持几何, 使控件入口保持在行数预算内。
// It must be declared beside the positioner, never inside it: a Row/Column would lay
// the pill out as one more cell. 它必须与定位器平级声明, 否则会被当成一个单元排版。
Rectangle {
    id: pill

    // ==================== Required Props 必需属性 ====================
    required property var selectorBar
    required property Item strip

    // ==================== Internal Props 内部属性 ====================
    // Selected cell; null while the strip is rebuilding 选中单元; 条带重建期间为空
    property Item target: null
    // Transitions run only after the first snap, and only when animation is allowed
    // 过渡仅在首次吸附之后、且允许动画时生效
    readonly property bool _animate:
        pill.selectorBar._pillReady && pill.selectorBar.pillAnimationEnabled

    // ==================== Size 尺寸 ====================
    x: pill.target ? pill.strip.x + pill.target.x : 0
    y: pill.selectorBar.vertical
        ? pill.strip.y + (pill.target ? pill.target.y : 0)
        : Enums.spacing.xxs
    width: pill.target ? pill.target.width : 0
    height: pill.selectorBar.vertical
        ? (pill.target ? pill.target.height : 0)
        : pill.selectorBar.height - Enums.spacing.xxs * 2
    radius: Enums.surfaceRadius(Enums.radius.small)
    visible: pill.target !== null
    color: Enums.stateColor.selectorBarItemSelected
    border.width: Enums.surfaceBorderWidth(Enums.border.thin)
    border.color: Enums.stateColor.selectorBarItemSelectedBorder

    // Geometry transition; timing and curve match the tab-switch slide
    // (Enums.duration.slow + OutCubic). The control latches its ready flag only after
    // the first snap, so the pill never slides in from the origin.
    // 几何过渡; 时长与曲线与标签页切换滑动一致(Enums.duration.slow + OutCubic)。控件在首次
    // 吸附之后才置位就绪标记, 因此胶囊不会从原点滑入。
    Behavior on x {
        enabled: pill._animate
        NumberAnimation { duration: Enums.duration.slow; easing.type: Easing.OutCubic }
    }
    Behavior on y {
        enabled: pill._animate
        NumberAnimation { duration: Enums.duration.slow; easing.type: Easing.OutCubic }
    }
    Behavior on width {
        enabled: pill._animate
        NumberAnimation { duration: Enums.duration.slow; easing.type: Easing.OutCubic }
    }
    Behavior on height {
        enabled: pill._animate
        NumberAnimation { duration: Enums.duration.slow; easing.type: Easing.OutCubic }
    }
}
