// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../buttons/Button"

// SpinBoxButton - Spin box increment/decrement button 微调框加减按钮
// Extends ButtonCore with transparent style 继承ButtonCore使用透明样式
ButtonCore {
    id: control
    
    // Transparent tool button style 透明工具按钮样式
    style: Enums.button.style_transparent
    
    // ==================== Size 尺寸 ====================
    // Override the base contentHeight/contentWidth calculation with preferredHeight 使用 preferredHeight 覆盖底层的 contentHeight/contentWidth 计算机制
    // Keep the button at 75% of the parent height with equal width 保持按钮高度为父容器的 75% 并采用等宽设计
    preferredHeight: parent ? parent.height * 0.75 : 24
    preferredWidth: preferredHeight
    
    // Auto adjust radius to keep it rounded 自动调整圆角（可选）
    radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small

}
