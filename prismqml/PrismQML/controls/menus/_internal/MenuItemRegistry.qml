// MenuItemRegistry - logical item ownership and measurement 菜单逻辑项所有权与测量
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick

QtObject {
    id: registry

    // ==================== Internal Props 内部属性 ====================
    property var items: []

    // ==================== Public Methods 公开方法 ====================
    function registerItem(item) {
        if (!item || items.indexOf(item) !== -1) return
        items = items.concat([item])
    }

    function unregisterItem(item) {
        var remaining = []
        for (var i = 0; i < items.length; i++) {
            var current = items[i]
            if (current && current !== item) remaining.push(current)
        }
        items = remaining
    }

    function liveItems() {
        var result = []
        for (var i = 0; i < items.length; i++) {
            if (items[i]) result.push(items[i])
        }
        items = result
        return result
    }

    function clear() {
        var result = liveItems()
        items = []
        return result
    }

    function measuredWidth(minimumWidth) {
        var width = minimumWidth
        var currentItems = liveItems()
        for (var i = 0; i < currentItems.length; i++) {
            if (currentItems[i].implicitWidth) {
                width = Math.max(width, currentItems[i].implicitWidth)
            }
        }
        return width
    }

    function measuredHeight() {
        var height = 0
        var currentItems = liveItems()
        for (var i = 0; i < currentItems.length; i++) {
            var item = currentItems[i]
            if (item.visible === false) continue
            var itemHeight = item.height > 0 ? item.height : item.implicitHeight
            if (itemHeight > 0) height += itemHeight
        }
        return height
    }
}
