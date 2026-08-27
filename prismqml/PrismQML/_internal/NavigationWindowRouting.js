// NavigationWindowRouting - Window page and bottom navigation routing 窗口页面与底部导航路由
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function moveDefaultPages(window, stagedItems, container, ownerName) {
    var pageSources = window["pageSources"]
    if (pageSources && typeof pageSources.length === "number" && pageSources.length > 0) return 0

    var items = []
    for (var index = 0; index < stagedItems.length; index++) {
        items.push(stagedItems[index])
    }

    var pageIndex = 0
    for (var sourceIndex = 0; sourceIndex < items.length; sourceIndex++) {
        if (window._moveDefaultPage(
                items[sourceIndex], container, pageIndex,
                sourceIndex, ownerName)) {
            pageIndex += 1
        }
    }
    return pageIndex
}

function safePageSources(pageSources) {
    return pageSources && typeof pageSources.length === "number"
        ? pageSources : []
}

function windowPageSources(window) {
    return safePageSources(window["pageSources"])
}

function resolveBottomPageIndex(item, pageSources) {
    if (!item || item.key === undefined || item.selectable === false) return -1

    var itemKey = String(item.key)
    // Prefer the Python window key format page_N. 优先解析 Python 窗口的 page_N 键格式。
    var match = itemKey.match(/^page_(\d+)$/)
    if (match) return parseInt(match[1], 10)

    // Otherwise search QML lazy-loading sources. 否则搜索 QML 懒加载源。
    var sources = safePageSources(pageSources)
    for (var index = 0; index < sources.length; index++) {
        var source = sources[index]
        if (source === null || source === undefined) continue
        if (String(source).indexOf(itemKey) !== -1) return index
    }
    return -1
}

function findBottomPageItem(window, pageIndex, pageSources) {
    for (var index = 0;
            index < window._safeBottomNavigationItems.length; index++) {
        var item = window._safeBottomNavigationItems[index]
        if (resolveBottomPageIndex(item, pageSources) === pageIndex) return item
    }
    return null
}

function syncSelection(window, pageIndex, navPanel, pageSources) {
    if (!navPanel) return false

    var item = findBottomPageItem(window, pageIndex, pageSources)
    if (!item) {
        if (navPanel["_currentKey"] !== undefined) navPanel._currentKey = ""
        if (navPanel["_bottomItemActive"] !== undefined) {
            navPanel._bottomItemActive = false
        }
        return false
    }

    // Keep the bottom delegate, selected icon, and indicator on the same source index.
    // 让底部委托、选中图标和指示器共同跟随同一个源索引。
    var oldMap = navPanel._bottomPageIndexMap || {}
    var map = ({})
    for (var key in oldMap) map[key] = oldMap[key]
    map[item.key] = pageIndex
    navPanel._bottomPageIndexMap = map
    if (navPanel["_currentKey"] !== undefined) {
        navPanel._currentKey = String(item.key)
    }
    if (navPanel["_bottomItemActive"] !== undefined) {
        navPanel._bottomItemActive = true
    }
    if (typeof navPanel.updateIndicatorForBottomItem === "function") {
        navPanel.updateIndicatorForBottomItem(item.key)
    }
    return true
}

function handleBottomItemClicked(window, index, navPanel, pageSources) {
    var item = window._safeBottomNavigationItems[index]
    var isPageItem = item && item.key !== undefined
    var isSelectable = item && item.selectable !== false

    if (!isPageItem || !isSelectable) {
        // Function items only emit the public signal. 功能项只发送公开信号。
        window.bottomItemClicked(index)
        return -1
    }

    var pageIndex = resolveBottomPageIndex(item, pageSources)
    if (pageIndex >= 0) {
        // Change the window source index only; direct stack writes would break its binding.
        // 只修改窗口源索引；直接写 stack 会破坏其声明式绑定。
        var changed = window.currentIndex !== pageIndex
        window.currentIndex = pageIndex
        // Re-selecting the active bottom page emits no currentIndex change; synchronize explicitly.
        // 再次选择当前底部页不会触发 currentIndex 变化，因此显式同步一次。
        if (!changed) syncSelection(window, pageIndex, navPanel, pageSources)
        window.currentPageChanged(pageIndex)
    }
    window.bottomItemClicked(index)
    return pageIndex
}
