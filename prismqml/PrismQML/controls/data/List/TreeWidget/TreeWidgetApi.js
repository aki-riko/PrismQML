// TreeWidgetApi.js - QTreeWidget API functions QTreeWidget API 函数
// Usage: import "TreeWidgetApi.js" as Api

// ==================== Top Level Items API 顶级项 API ====================

function topLevelItemCount(ctrl) {
    return ctrl.model ? ctrl.model.length : 0
}

function topLevelItem(ctrl, index) {
    if (!ctrl.model || index < 0 || index >= ctrl.model.length) return null
    return ctrl.model[index]
}

function addTopLevelItem(ctrl, item) {
    if (!ctrl.model) ctrl.model = []
    ctrl.model.push(ctrl._normalizeItem(item))
    ctrl.model = ctrl.model.slice()
    ctrl._rebuildModel()
}

function addTopLevelItems(ctrl, items) {
    for (var i = 0; i < items.length; i++) {
        addTopLevelItem(ctrl, items[i])
    }
}

function insertTopLevelItem(ctrl, index, item) {
    if (!ctrl.model) ctrl.model = []
    if (index < 0) index = 0
    if (index > ctrl.model.length) index = ctrl.model.length
    ctrl.model.splice(index, 0, ctrl._normalizeItem(item))
    ctrl.model = ctrl.model.slice()
    ctrl._rebuildModel()
}

function insertTopLevelItems(ctrl, index, items) {
    for (var i = 0; i < items.length; i++) {
        insertTopLevelItem(ctrl, index + i, items[i])
    }
}

function takeTopLevelItem(ctrl, index) {
    if (!ctrl.model || index < 0 || index >= ctrl.model.length) return null
    var item = ctrl.model.splice(index, 1)[0]
    ctrl.model = ctrl.model.slice()
    ctrl._rebuildModel()
    return item
}

function indexOfTopLevelItem(ctrl, item) {
    if (!ctrl.model) return -1
    var searchText = typeof item === "string" ? item : (item.text || "")
    for (var i = 0; i < ctrl.model.length; i++) {
        if ((ctrl.model[i].text || "") === searchText) return i
    }
    return -1
}

// ==================== Current Item API 当前项 API ====================

function currentItem(ctrl) {
    return ctrl._getItemObject(ctrl.currentIndex)
}

function setCurrentItem(ctrl, item) {
    var idx = ctrl._findItemIndex(item)
    if (idx >= 0) {
        ctrl.currentIndex = idx
        ctrl._selectedIndices = [idx]
    }
}

// ==================== Selection API 选择 API ====================

function selectedItems(ctrl, internalModel) {
    var result = []
    for (var i = 0; i < ctrl._selectedIndices.length; i++) {
        var it = ctrl._getItemObject(ctrl._selectedIndices[i])
        if (it) result.push(it)
    }
    return result
}

function clearSelection(ctrl) {
    ctrl._selectedIndices = []
    ctrl.currentIndex = -1
    ctrl.itemSelectionChanged()
}

function selectAll(ctrl, internalModel) {
    if (ctrl.selectionMode === ctrl.noSelection || ctrl.selectionMode === ctrl.singleSelection) return
    ctrl._selectedIndices = []
    for (var i = 0; i < internalModel.count; i++) {
        ctrl._selectedIndices.push(i)
    }
    ctrl.itemSelectionChanged()
}

function setSelectionMode(ctrl, mode) {
    ctrl.selectionMode = mode
    if (mode === ctrl.singleSelection && ctrl._selectedIndices.length > 1) {
        ctrl._selectedIndices = ctrl.currentIndex >= 0 ? [ctrl.currentIndex] : []
    }
}

// ==================== Expand/Collapse API 展开/收起 API ====================

function expandItem(ctrl, internalModel, item) {
    var idx = ctrl._findItemIndex(item)
    if (idx >= 0 && internalModel.get(idx).hasChildren && !internalModel.get(idx).expanded) {
        ctrl._toggleExpandAt(idx)
    }
}

function collapseItem(ctrl, internalModel, item) {
    var idx = ctrl._findItemIndex(item)
    if (idx >= 0 && internalModel.get(idx).hasChildren && internalModel.get(idx).expanded) {
        ctrl._toggleExpandAt(idx)
    }
}

function expandAll(ctrl) {
    ctrl._setExpandedRecursive(ctrl.model, true)
    ctrl._rebuildModel()
}

function collapseAll(ctrl) {
    ctrl._setExpandedRecursive(ctrl.model, false)
    ctrl._rebuildModel()
}

function isItemExpanded(ctrl, internalModel, item) {
    var idx = ctrl._findItemIndex(item)
    return idx >= 0 ? internalModel.get(idx).expanded : false
}

function setItemExpanded(ctrl, internalModel, item, expanded) {
    var idx = ctrl._findItemIndex(item)
    if (idx >= 0 && internalModel.get(idx).expanded !== expanded) {
        ctrl._toggleExpandAt(idx)
    }
}

// ==================== Find API 查找 API ====================

function findItems(ctrl, internalModel, text, flags, column) {
    var result = []
    var pattern = text.toLowerCase()
    for (var i = 0; i < internalModel.count; i++) {
        var itemText = (internalModel.get(i).text || "").toLowerCase()
        var match = false
        if (flags === 0) match = (itemText === pattern)
        else if (flags === 1) match = (itemText.indexOf(pattern) >= 0)
        else if (flags === 2) match = itemText.startsWith(pattern)
        else if (flags === 3) match = itemText.endsWith(pattern)
        else if (flags === 4) match = new RegExp(text).test(itemText)
        if (match) result.push(ctrl._getItemObject(i))
    }
    return result
}

// ==================== Sorting API 排序 API ====================

function sortItems(ctrl, column, order) {
    if (!ctrl.model) return
    ctrl._sortRecursive(ctrl.model, order)
    ctrl.model = ctrl.model.slice()
    ctrl._rebuildModel()
}

// ==================== Headers API 表头 API ====================

function setHeaderLabels(ctrl, labels) {
    ctrl.headerLabels = labels.slice()
    ctrl.columnCount = labels.length
}

function setHeaderLabel(ctrl, label) {
    ctrl.headerLabels = [label]
    ctrl.columnCount = 1
}

function headerItem(ctrl) {
    return { labels: ctrl.headerLabels }
}

// ==================== Clear/Count API 清空/计数 API ====================

function clear(ctrl, internalModel) {
    ctrl.model = []
    internalModel.clear()
    ctrl._selectedIndices = []
    ctrl.currentIndex = -1
}

function count(internalModel) {
    return internalModel.count
}

// ==================== Item Properties API 项属性 API ====================

function setItemText(ctrl, internalModel, item, column, text) {
    var original = typeof item === "object" ? ctrl._findOriginalItem(item.pathStr) : null
    if (original) {
        original.text = text
        var idx = ctrl._findItemIndex(item)
        if (idx >= 0) internalModel.setProperty(idx, "text", text)
    }
}

function itemText(item, column) {
    return item ? item.text : ""
}

function setItemIcon(ctrl, internalModel, item, column, icon) {
    var original = typeof item === "object" ? ctrl._findOriginalItem(item.pathStr) : null
    if (original) {
        original.icon = icon
        var idx = ctrl._findItemIndex(item)
        if (idx >= 0) internalModel.setProperty(idx, "icon", icon)
    }
}

function setItemCheckState(ctrl, internalModel, item, column, state) {
    var original = typeof item === "object" ? ctrl._findOriginalItem(item.pathStr) : null
    if (original) {
        original.checkState = state
        original.checked = state
        var idx = ctrl._findItemIndex(item)
        if (idx >= 0) internalModel.setProperty(idx, "checkState", state)
    }
}

function itemCheckState(item, column) {
    return item ? item.checkState : 0
}

function setItemData(ctrl, item, column, role, value) {
    var original = typeof item === "object" ? ctrl._findOriginalItem(item.pathStr) : null
    if (original) {
        if (!original.data) original.data = {}
        original.data[role] = value
    }
}

function itemData(item, column, role) {
    return (item && item.data) ? item.data[role] : undefined
}

// ==================== Appearance API 外观 API ====================

function setBorderVisible(ctrl, visible) {
    ctrl.borderVisible = visible
}

function setBorderRadius(ctrl, r) {
    ctrl.borderRadius = r
}

function setIndentation(ctrl, indent) {
    ctrl.indentWidth = indent
}

function indentation(ctrl) {
    return ctrl.indentWidth
}

// ==================== Scroll API 滚动 API ====================

function scrollToItem(ctrl, listView, item, hint) {
    var idx = ctrl._findItemIndex(item)
    if (idx >= 0) listView.positionViewAtIndex(idx, 1)  // ListView.Center = 1
}

function scrollToTop(listView) {
    listView.positionViewAtBeginning()
}

function scrollToBottom(listView) {
    listView.positionViewAtEnd()
}
