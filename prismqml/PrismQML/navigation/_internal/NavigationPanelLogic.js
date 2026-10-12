// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// NavigationPanelLogic - Pure helpers for navigation panels 导航面板纯逻辑辅助

function isNavigationItemVisible(item) {
    return !!item && item.visible !== false
}

function createItem(key, icon, text, onClick, selectable, selectedIcon, visible) {
    return {
        "key": key,
        "icon": icon || "",
        "text": text || "",
        "selectedIcon": selectedIcon || icon || "",
        "selectable": selectable !== false,
        "visible": visible !== false,
        "onClick": onClick
    }
}

function routeMapFor(items) {
    var routeMap = {}
    for (var index = 0; index < items.length; index++) {
        if (items[index] && items[index].key) {
            routeMap[items[index].key] = index
        }
    }
    return routeMap
}

function indexForKeyOrText(items, key) {
    for (var index = 0; index < items.length; index++) {
        var item = items[index]
        if (item && (item.text === key || item.key === key)) return index
    }
    return -1
}

function itemAt(topRepeater, bottomRepeater, modelLength, index) {
    if (!topRepeater) return null

    if (index >= 0 && index < topRepeater.count) {
        return topRepeater.itemAt(index)
    } else if (bottomRepeater) {
        var bottomIndex = index - modelLength
        if (bottomIndex >= 0 && bottomIndex < bottomRepeater.count) {
            return bottomRepeater.itemAt(bottomIndex)
        }
    }
    return null
}

function bottomItemForKey(items, repeater, key) {
    if (!repeater || !key) return null
    for (var index = 0; index < (items || []).length; index++) {
        var item = (items || [])[index]
        if (item && item.key === key) return repeater.itemAt(index)
    }
    return null
}

function bottomIndexForKey(items, key) {
    if (!key) return -1
    for (var index = 0; index < (items || []).length; index++) {
        var item = (items || [])[index]
        if (item && item.key === key) return index
    }
    return -1
}

function itemForKey(items, keyMap, key) {
    var index = keyMap[key]
    if (index !== undefined && index < items.length) return items[index]
    return null
}

function indicatorRect(item, control, indicatorX, indicatorWidth, indicatorHeight) {
    if (!item) return Qt.rect(0, 0, 0, 0)

    var mappedPos = item.mapToItem(control, 0, 0)
    var y = mappedPos.y + (item.height - indicatorHeight) / 2
    return Qt.rect(indicatorX, y, indicatorWidth, indicatorHeight)
}
