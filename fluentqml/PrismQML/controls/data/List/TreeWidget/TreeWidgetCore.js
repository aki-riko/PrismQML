// TreeWidgetCore.js - Core internal functions 核心内部函数
// Usage: import "TreeWidgetCore.js" as Core

// ==================== Model Functions 模型函数 ====================

function rebuildModel(ctrl, internalModel) {
    internalModel.clear()
    if (!ctrl.model || ctrl.model.length === 0) return
    var flat = flattenModel(ctrl.model, 0, [])
    for (var i = 0; i < flat.length; i++) {
        var item = flat[i]
        internalModel.append({
            text: item.text || "",
            icon: item.icon || "",
            depth: item.depth || 0,
            hasChildren: (item.children && item.children.length > 0) ? true : false,
            expanded: item.expanded === true,
            checkable: item.checkable === true,
            checkState: item.checkState || item.checked || 0,
            pathStr: item.path ? item.path.join(",") : "",
            data: item.data || {}
        })
    }
}

function flattenModel(items, depth, path) {
    var result = []
    if (!items) return result
    for (var i = 0; i < items.length; i++) {
        var item = items[i]
        item.depth = depth
        item.path = path.concat([i])
        result.push(item)
        if (item.children && item.children.length > 0 && item.expanded === true) {
            result = result.concat(flattenModel(item.children, depth + 1, item.path))
        }
    }
    return result
}

function findOriginalItem(ctrl, pathStr) {
    if (!pathStr) return null
    var path = pathStr.split(",").map(function (x) { return parseInt(x) })
    var target = ctrl.model
    for (var i = 0; i < path.length - 1; i++) {
        if (!target[path[i]]) return null
        target = target[path[i]].children
    }
    return target ? target[path[path.length - 1]] : null
}

function normalizeItem(item) {
    if (typeof item === "string") {
        return { text: item, icon: "", children: [], expanded: false, checkable: false, checkState: 0, data: {} }
    }
    return {
        text: item.text || "",
        icon: item.icon || "",
        children: item.children || [],
        expanded: item.expanded || false,
        checkable: item.checkable || false,
        checkState: item.checkState || item.checked || 0,
        data: item.data || {}
    }
}

function findItemIndex(internalModel, item) {
    if (!item) return -1
    var searchText = typeof item === "string" ? item : (item.text || "")
    for (var i = 0; i < internalModel.count; i++) {
        if (internalModel.get(i).text === searchText) return i
    }
    return -1
}

function setExpandedRecursive(items, expanded) {
    if (!items) return
    for (var i = 0; i < items.length; i++) {
        items[i].expanded = expanded
        if (items[i].children) setExpandedRecursive(items[i].children, expanded)
    }
}

function sortRecursive(items, order) {
    if (!items) return
    items.sort(function (a, b) {
        var cmp = (a.text || "").localeCompare(b.text || "")
        return order === 1 ? -cmp : cmp
    })
    for (var i = 0; i < items.length; i++) {
        if (items[i].children) sortRecursive(items[i].children, order)
    }
}

// ==================== Selection Functions 选择函数 ====================

function isIndexSelected(ctrl, idx) {
    if (ctrl.selectionMode === ctrl.noSelection) return false
    if (ctrl.selectionMode === ctrl.singleSelection) return ctrl.currentIndex === idx
    return ctrl._selectedIndices.indexOf(idx) >= 0
}

function handleItemClick(ctrl, internalModel, idx, button, modifiers) {
    if (ctrl.selectionMode === ctrl.noSelection) return
    if (button === 2 && !ctrl.selectOnRightClick) return  // Qt.RightButton = 2

    var prevItem = getItemObject(ctrl, internalModel, ctrl.currentIndex)

    if (ctrl.selectionMode === ctrl.singleSelection) {
        ctrl.currentIndex = idx
        ctrl._selectedIndices = [idx]
    } else if (ctrl.selectionMode === ctrl.multiSelection) {
        var i = ctrl._selectedIndices.indexOf(idx)
        if (i >= 0) ctrl._selectedIndices.splice(i, 1)
        else ctrl._selectedIndices.push(idx)
        ctrl._selectedIndices = ctrl._selectedIndices.slice()
        ctrl.currentIndex = idx
    } else if (ctrl.selectionMode === ctrl.extendedSelection) {
        if (modifiers & 0x04000000) {  // Qt.ControlModifier
            var j = ctrl._selectedIndices.indexOf(idx)
            if (j >= 0) ctrl._selectedIndices.splice(j, 1)
            else ctrl._selectedIndices.push(idx)
            ctrl._selectedIndices = ctrl._selectedIndices.slice()
        } else if ((modifiers & 0x02000000) && ctrl.currentIndex >= 0) {  // Qt.ShiftModifier
            var start = Math.min(ctrl.currentIndex, idx)
            var end = Math.max(ctrl.currentIndex, idx)
            ctrl._selectedIndices = []
            for (var k = start; k <= end; k++) ctrl._selectedIndices.push(k)
        } else {
            ctrl._selectedIndices = [idx]
        }
        ctrl.currentIndex = idx
    }

    var currItem = getItemObject(ctrl, internalModel, idx)
    if (prevItem !== currItem) {
        ctrl.currentItemChanged(currItem, prevItem)
    }
    ctrl._previousItem = currItem
    ctrl.itemSelectionChanged()
}

function getItemObject(ctrl, internalModel, idx) {
    if (idx < 0 || idx >= internalModel.count) return null
    var m = internalModel.get(idx)
    return {
        text: m.text,
        icon: m.icon,
        depth: m.depth,
        hasChildren: m.hasChildren,
        expanded: m.expanded,
        checkState: m.checkState,
        data: m.data,
        pathStr: m.pathStr,
        index: idx
    }
}

// ==================== Toggle Functions 切换函数 ====================

function toggleExpandAt(ctrl, internalModel, idx) {
    var item = internalModel.get(idx)
    if (!item) return
    var original = findOriginalItem(ctrl, item.pathStr)
    if (!original) return

    var wasExpanded = original.expanded === true
    original.expanded = !wasExpanded
    internalModel.setProperty(idx, "expanded", !wasExpanded)

    if (wasExpanded) {
        var removeCount = 0
        var basePath = item.pathStr + ","
        for (var j = idx + 1; j < internalModel.count; j++) {
            if (internalModel.get(j).pathStr.indexOf(basePath) === 0) removeCount++
            else break
        }

        if (ctrl.currentIndex > idx && ctrl.currentIndex <= idx + removeCount) {
            ctrl.currentIndex = -1
            ctrl._selectedIndices = []
        } else if (ctrl.currentIndex > idx + removeCount) {
            ctrl.currentIndex = ctrl.currentIndex - removeCount
        }

        for (var k = 0; k < removeCount; k++) internalModel.remove(idx + 1)
        ctrl.itemCollapsed(original)
    } else {
        var children = flattenModel(original.children, item.depth + 1, original.path)
        for (var m = 0; m < children.length; m++) {
            var c = children[m]
            internalModel.insert(idx + 1 + m, {
                text: c.text || "",
                icon: c.icon || "",
                depth: c.depth || 0,
                hasChildren: (c.children && c.children.length > 0) ? true : false,
                expanded: c.expanded === true,
                checkable: c.checkable === true,
                checkState: c.checkState || c.checked || 0,
                pathStr: c.path ? c.path.join(",") : "",
                data: c.data || {}
            })
        }
        ctrl.itemExpanded(original)
    }
}

function toggleCheckAt(ctrl, internalModel, idx) {
    var item = internalModel.get(idx)
    if (!item) return
    var original = findOriginalItem(ctrl, item.pathStr)
    if (!original) return
    var newState = (item.checkState === 2) ? 0 : 2
    original.checkState = newState
    original.checked = newState
    internalModel.setProperty(idx, "checkState", newState)
    ctrl.itemChecked(original, newState)
}
