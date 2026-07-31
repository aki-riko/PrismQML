// TreeWidgetCore.js - Core internal functions 核心内部函数
// Usage: import "TreeWidgetCore.js" as Core

var nextTreeItemId = 1

// ==================== Model Functions 模型函数 ====================

function ensureItemIdentity(item) {
    if (!item || typeof item !== "object") return -1
    if (item._treeItemId === undefined || item._treeItemId === null) {
        item._treeItemId = nextTreeItemId
        nextTreeItemId += 1
    }
    return item._treeItemId
}

function rebuildModel(ctrl, internalModel) {
    internalModel.clear()
    var sourceModel = ctrl.model
    if (!sourceModel || typeof sourceModel.length !== "number") sourceModel = []
    if (sourceModel.length === 0) return
    var flat = flattenModel(sourceModel, 0, [])
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
            data: item.data || {},
            _treeItemId: ensureItemIdentity(item)
        })
    }
}

function flattenModel(items, depth, path, result) {
    if (!result) result = []
    if (!items) return result
    for (var i = 0; i < items.length; i++) {
        var item = items[i]
        if (item === null || item === undefined) continue
        if (typeof item === "string") item = {text: item}
        if (typeof item !== "object") continue
        ensureItemIdentity(item)
        item.depth = depth
        item.path = path.concat([i])
        result.push(item)
        if (item.children && item.children.length > 0 && item.expanded === true) {
            flattenModel(item.children, depth + 1, item.path, result)
        }
    }
    return result
}

function findOriginalItem(ctrl, pathStr) {
    if (!pathStr) return null
    var path = pathStr.split(",").map(function (x) { return parseInt(x) })
    var target = ctrl.model
    if (!target || typeof target.length !== "number") return null
    for (var i = 0; i < path.length - 1; i++) {
        var parent = target[path[i]]
        if (!parent || typeof parent !== "object" || !parent.children ||
                typeof parent.children.length !== "number") return null
        target = parent.children
    }
    if (!target || typeof target.length !== "number") return null
    return target[path[path.length - 1]] || null
}

function normalizeItem(item) {
    if (typeof item === "string") {
        return { text: item, icon: "", children: [], expanded: false, checkable: false, checkState: 0, data: {} }
    }
    if (!item || typeof item !== "object") {
        return { text: "", icon: "", children: [], expanded: false, checkable: false, checkState: 0, data: {} }
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

function itemPathString(item) {
    if (!item || typeof item !== "object") return ""
    if (item.pathStr !== undefined && item.pathStr !== null && String(item.pathStr) !== "") {
        return String(item.pathStr)
    }
    if (item.path && typeof item.path.join === "function") return item.path.join(",")
    return ""
}

function findItemIndex(internalModel, item) {
    if (!item) return -1
    if (typeof item === "object" && item._treeItemId !== undefined && item._treeItemId !== null) {
        for (var identityIndex = 0; identityIndex < internalModel.count; identityIndex++) {
            if (internalModel.get(identityIndex)._treeItemId === item._treeItemId) return identityIndex
        }
        return -1
    }
    var searchPath = itemPathString(item)
    if (searchPath !== "") {
        for (var pathIndex = 0; pathIndex < internalModel.count; pathIndex++) {
            if (internalModel.get(pathIndex).pathStr === searchPath) return pathIndex
        }
        return -1
    }
    var searchText = typeof item === "string" ? item : (item.text || "")
    for (var i = 0; i < internalModel.count; i++) {
        if (internalModel.get(i).text === searchText) return i
    }
    return -1
}

function setExpandedRecursive(items, expanded) {
    if (!items) return
    for (var i = 0; i < items.length; i++) {
        if (!items[i] || typeof items[i] !== "object") continue
        items[i].expanded = expanded
        if (items[i].children) setExpandedRecursive(items[i].children, expanded)
    }
}

function sortRecursive(items, order) {
    if (!items) return
    items.sort(function (a, b) {
        var cmp = ((a && a.text) || "").localeCompare((b && b.text) || "")
        return order === 1 ? -cmp : cmp
    })
    for (var i = 0; i < items.length; i++) {
        if (items[i] && items[i].children) sortRecursive(items[i].children, order)
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
        _treeItemId: m._treeItemId,
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

        if (removeCount > 0) internalModel.remove(idx + 1, removeCount)
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
                data: c.data || {},
                _treeItemId: ensureItemIdentity(c)
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
