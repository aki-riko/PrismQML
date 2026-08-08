// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "."

// SystemTrayMenu - System tray context menu 系统托盘上下文菜单
// Inherits from MenuCore with optimizations for system tray usage 继承自MenuCore，针对系统托盘使用进行优化
MenuCore {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property bool showAtCursor: true
    property var initialActions: []

    // ==================== Readonly State 只读状态 ====================
    readonly property var _safeInitialActions:
        initialActions === null || initialActions === undefined ? []
        : (typeof initialActions.length === "number" ? initialActions : [])
    
    // ==================== Public Methods 公开方法 ====================
    function showAtPosition(x, y) {
        // 彻底重置旧状态（停止动画 + 隐藏旧窗口 + 清除标志）
        forceReset()
        
        // Ensure menu items are visible to the size pass before positioning.
        // 定位前先创建内容宿主，让尺寸计算能看到菜单项。
        if (!_usesControlsPopup) _ensureNativeWindow()

        // 重新计算尺寸
        _updateSize()
        
        var menuHeight = popupHeight
        
        // 上拉定位：菜单出现在点击位置上方
        var posX = x
        var posY = y - menuHeight - Enums.spacing.xs
        
        // Flip below the click only when there is no room above. 上方空间不足时才翻转到点击点下方
        var bounds = _screenBoundsAt(x, y, null)
        if (bounds && posY < bounds.top) posY = y + Enums.spacing.xs
        
        open(posX, posY)
    }

    constrainToAvailableScreen: false
    closeOnClickOutside: true
    Component.onCompleted: {
        if (_safeInitialActions.length > 0) addActions(_safeInitialActions)
    }
}
