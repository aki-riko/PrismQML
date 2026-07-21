// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../buttons/Button"

// MiniSpinButton - Small spin box up/down button 小型微调框上下按钮
// Extends ButtonCore with transparent style 继承ButtonCore使用透明样式
ButtonCore {
    id: control
    
    // Transparent tool button style 透明工具按钮样式
    style: Enums.button.style_transparent
    iconSize: Enums.iconSize.micro  // 8
    
    // ==================== Size 尺寸 ====================
    // The parent assigns explicit half-height width/height values to compact buttons 父级通过明确的 width/height 为紧凑按钮分配半高尺寸
    radius: Enums.radius.tiny

}
