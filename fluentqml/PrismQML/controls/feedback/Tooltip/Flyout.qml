// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// Flyout - Popup layer component (based on TipPopup) 弹出层组件
// Simple popup without arrow, supports multiple animation types 无箭头的简单弹出提示，支持多种动画类型

TipPopup {
    id: control
    tipType: Enums.tip.type_flyout
    
    // Flyout specific properties Flyout特有属性
    // animationType is defined in TipPopup 已在TipPopup中定义
    // Supports: pullUp / dropDown / slideLeft / slideRight / fadeIn / none 支持: pullUp / dropDown / slideLeft / slideRight / fadeIn / none

}
