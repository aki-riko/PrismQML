// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

pragma Singleton
import QtQuick

// PopupUtils - 弹出层公共工具
QtObject {

    // Find child by name 按名称查找子元素
    function findChildByName(parent, name) {
        if (!parent || !parent.children) return null
        for (var i = 0; i < parent.children.length; i++) {
            var child = parent.children[i]
            if (child.objectName === name) return child
            var found = findChildByName(child, name)
            if (found) return found
        }
        return null
    }
    
    // Calculate popup position (4px below, compensate shadow) 计算弹出位置
    function calcPopupPos(control) {
        var globalPos = control.mapToGlobal(0, control.height + 4)
        return { x: globalPos.x - 8, y: globalPos.y - 8 }
    }
}
