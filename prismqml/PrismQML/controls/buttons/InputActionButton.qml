// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "Button"

// InputActionButton - Action button for input fields 输入框操作按钮
// Used for password toggle, search, etc. 用于密码切换、搜索等
ButtonCore {
    id: control
    
    // ==================== Props 属性 ====================
    property bool collapsed: false  // Collapsed mode (for search) 折叠模式
    property int collapsedSize: Enums.controlSize.inputHeight  // Collapsed size 折叠尺寸
    
    // ==================== Style 样式 ====================
    style: Enums.button.style_transparent
    
    // ==================== Size 尺寸 ====================
    // 高度限制为父容器 75%，宽高一致保持正方形
    preferredHeight: collapsed ? collapsedSize : (parent ? parent.height * 0.75 : Enums.controlSize.closeButtonSize)
    preferredWidth: preferredHeight
    
    // Collapsed mode: pill shape for rounded look 折叠模式：药丸形状
    shape: collapsed ? Enums.button.shape_pill : Enums.button.shape_default
}
