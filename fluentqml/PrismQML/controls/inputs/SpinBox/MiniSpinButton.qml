// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../buttons/Button"

// MiniSpinButton - Small spin box up/down button 小型微调框上下按钮
// Extends ButtonCore with transparent style 继承ButtonCore使用透明样式
ButtonCore {
    id: control
    
    // ==================== Transparent Tool Button Style 透明工具按钮样式 ====================
    style: Enums.button.style_transparent
    iconSize: Enums.iconSize.micro  // 8
    
    // ==================== Size Override 尺寸覆盖 ====================
    // compact 按钮固定在父类通过明确的 width/height 锚定分半赋值
    radius: Enums.radius.tiny

    // 双击当作两次单击处理: 否则 MouseArea 在 doubleClickInterval (≈400ms) 内的
    // 第二次点击只会触发 doubleClicked,不会触发 clicked,导致快速连点 +/- 吞点击
    onDoubleClicked: clicked()
}
