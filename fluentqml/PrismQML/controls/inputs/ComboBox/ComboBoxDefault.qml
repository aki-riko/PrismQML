// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."

// ComboBoxDefault - Default combo box with style/feature support 默认下拉框
ComboBoxCore {
    id: control
    
    // ==================== Style/Feature Props 样式/功能属性 ====================
    // Use 0 as default to avoid Enums init timing issue 使用0避免初始化时序问题
    style: 0  // 0 = style_default
    feature: 0  // 0 = feature_none
    
    // ==================== Editable 可编辑 ====================
    editable: feature === 1
}
