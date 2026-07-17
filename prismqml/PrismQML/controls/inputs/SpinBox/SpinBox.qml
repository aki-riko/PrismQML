// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."

// SpinBox - Unified spin box component 统一微调框组件
// Control via type property 通过type属性控制类型
// Types 类型: spinbox_normal, spinbox_double, spinbox_compact, spinbox_compact_double
SpinBoxCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int type: Enums.input.spinbox_normal

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isDouble: type === Enums.input.spinbox_double ||
                                      type === Enums.input.spinbox_compact_double
    readonly property bool _isCompact: type === Enums.input.spinbox_compact ||
                                       type === Enums.input.spinbox_compact_double

    // Apply type configuration 应用类型配置
    decimals: _isDouble ? Enums.input.spinBoxDoubleDecimals : Enums.input.spinBoxIntegerDecimals
    stepSize: _isDouble ? Enums.input.spinBoxDoubleStep : Enums.input.spinBoxIntegerStep
    compactMode: _isCompact  // Compact mode with inline up/down buttons 紧凑模式带内联上下按钮

    // ==================== Size 尺寸 ====================
    implicitWidth: _isCompact
        ? (_isDouble
            ? Enums.controlSize.spinBoxCompactWidth + Enums.controlSize.spinBoxCompactDoubleExtraWidth
            : Enums.controlSize.spinBoxCompactWidth)
        : Enums.controlSize.spinBoxWidth
    implicitHeight: _isCompact ? Enums.controlSize.inputHeightCompact : Enums.controlSize.inputHeight
}
