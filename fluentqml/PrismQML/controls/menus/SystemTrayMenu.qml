// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "."

// SystemTrayMenu - System tray context menu 系统托盘上下文菜单
// Inherits from MenuCore with optimizations for system tray usage 继承自MenuCore，针对系统托盘使用进行优化
MenuCore {
    id: control
    
    // ==================== System Tray Specific Props 系统托盘特定属性 ====================
    property bool showAtCursor: true
    closeOnClickOutside: true
    
    // ==================== Public Methods 公开方法 ====================
    function showAtPosition(x, y) {
        // 彻底重置旧状态（停止动画 + 隐藏旧窗口 + 清除标志）
        forceReset()
        
        // 重新计算尺寸
        _updateSize()
        
        var menuHeight = popupHeight
        var menuWidth = popupWidth
        
        // 上拉定位：菜单出现在点击位置上方
        var posX = x
        var posY = y - menuHeight - Enums.spacing.xs
        
        // 使用 Qt.application.screens 做边界检查
        var screen = Qt.application.screens[0]
        if (screen) {
            if (posY < 0) posY = y + Enums.spacing.xs
            if (posX + menuWidth > screen.width) posX = screen.width - menuWidth - Enums.spacing.xs
            if (posX < 0) posX = Enums.spacing.xs
        }
        
        open(posX, posY)
    }
    
    // Alias for compatibility 兼容别名
    function exec(pos) {
        if (pos) {
            showAtPosition(pos.x, pos.y)
        } else {
            openAtMouse()
        }
    }
}
