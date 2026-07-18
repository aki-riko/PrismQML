// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "Button"

// InputActionButton - Action button for input fields 输入框操作按钮
// Used for password toggle, search, etc. 用于密码切换、搜索等
ButtonCore {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property bool collapsed: false  // Collapsed mode (for search) 折叠模式
    property int collapsedSize: Enums.controlSize.inputHeight  // Collapsed size 折叠尺寸
    property bool fillParentHeight: false  // Match the parent input height 匹配父输入框高度
    
    // Style 样式
    style: Enums.button.style_transparent
    
    // ==================== Size 尺寸 ====================
    // Keep compact by default; collapsible search can fill the input height
    // 默认保持紧凑；可折叠搜索框可填满输入框高度
    preferredHeight: collapsed ? collapsedSize
        : (fillParentHeight && parent ? parent.height
           : (parent ? parent.height * 0.75 : Enums.controlSize.closeButtonSize))
    preferredWidth: preferredHeight
    
    // Collapsed mode: pill shape for rounded look 折叠模式：药丸形状
    shape: collapsed ? Enums.button.shape_pill : Enums.button.shape_default
}
