// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../buttons/Button"

// SpinBoxButton - Spin box increment/decrement button 微调框加减按钮
// Extends ButtonCore with transparent style 继承ButtonCore使用透明样式
ButtonCore {
    id: control
    
    // ==================== Transparent Tool Button Style 透明工具按钮样式 ====================
    style: Enums.button.style_transparent
    
    // ==================== Size Override 尺寸覆盖 ====================
    // 使用 preferredHeight 强制截断底层的 contentHeight/contentWidth 计算机制
    // 满足高度为父容器 75% 且等宽的正方形设计
    preferredHeight: parent ? parent.height * 0.75 : 24
    preferredWidth: preferredHeight
    
    // Auto adjust radius to keep it rounded 自动调整圆角（可选）
    radius: Enums.radius.small

    // 双击当作两次单击处理: 否则 MouseArea 在 doubleClickInterval (≈400ms) 内的
    // 第二次点击只会触发 doubleClicked,不会触发 clicked,导致快速连点 +/- 吞点击
    onDoubleClicked: clicked()
}
