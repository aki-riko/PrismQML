// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."

// SpinBox - Unified spin box component 统一微调框组件
// Control via type property 通过type属性控制类型
// Types 类型: spinbox_normal, spinbox_double, spinbox_compact, spinbox_compact_double
SpinBoxCore {
    id: control
    
    // ==================== Type Prop 类型属性 ====================
    property int type: Enums.input.spinbox_normal
    
    // ==================== Type-based Configuration 基于类型的配置 ====================
    readonly property bool _isDouble: type === Enums.input.spinbox_double || 
                                      type === Enums.input.spinbox_compact_double
    readonly property bool _isCompact: type === Enums.input.spinbox_compact || 
                                       type === Enums.input.spinbox_compact_double
    
    // ==================== Apply Type Settings 应用类型设置 ====================
    decimals: _isDouble ? 2 : 0
    stepSize: _isDouble ? 0.1 : 1
    compactMode: _isCompact  // Compact mode with inline up/down buttons 紧凑模式带内联上下按钮
    
    // ==================== Size Override 尺寸覆盖 ====================
    implicitWidth: _isCompact ? (_isDouble ? Enums.controlSize.spinBoxCompactWidth + 10 : Enums.controlSize.spinBoxCompactWidth) : Enums.controlSize.spinBoxWidth
    implicitHeight: _isCompact ? 28 : Enums.controlSize.inputHeight
}
