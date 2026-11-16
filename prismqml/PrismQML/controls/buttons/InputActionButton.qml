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
    // Item whose height sizes the button; defaults to the parent, a Loader host
    // passes the input instead. 用于计算尺寸的高度来源；默认是父对象，经 Loader 加载时传入输入框。
    property Item sizingParent: parent

    // Match regular Button hover feedback only while collapsed.
    // 仅在收起态匹配普通 Button 的悬浮反馈。
    style: collapsed ? Enums.button.style_default : Enums.button.style_transparent
    
    // ==================== Size 尺寸 ====================
    // Keep compact by default; collapsible search can fill the input height
    // 默认保持紧凑；可折叠搜索框可填满输入框高度
    preferredHeight: collapsed ? collapsedSize
        : (fillParentHeight && sizingParent ? sizingParent.height
           : (sizingParent ? sizingParent.height * 0.75 : Enums.controlSize.closeButtonSize))
    preferredWidth: preferredHeight
    
    // Keep the collapsed search surface filled with the input's square bounds.
    // 收起态搜索面保持填满输入框的方形边界。
    shape: Enums.button.shape_default
}
