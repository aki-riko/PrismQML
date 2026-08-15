// ListDataController - List model and selection helpers 列表模型与选择辅助
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function _normalizeItem(item) {
    if (typeof item === "string") {
        return {
            text: item, icon: "", data: {}, checkable: false,
            checkState: 0, selected: false, flags: 0
        }
    }
    if (!item || typeof item !== "object") {
        return {
            text: "", icon: "", data: {}, checkable: false,
            checkState: 0, selected: false, flags: 0
        }
    }
    return {
        text: item.text || "",
        icon: item.icon || item.iconSource || "",
        data: item.data || {},
        checkable: item.checkable || false,
        checkState: item.checkState || item.checked || 0,
        selected: item.selected || false,
        flags: item.flags || 0
    }
}

function _getItemObject(control, row) {
    var listModel = control._listModel
    if (row < 0 || row >= listModel.count) return null
    var modelItem = listModel.get(row)
    return {
        text: modelItem.text,
        icon: modelItem.icon,
        data: modelItem.data,
        checkable: modelItem.checkable,
        checkState: modelItem.checkState,
        selected: control._isRowSelected(row),
        flags: modelItem.flags,
        row: row
    }
}

function addItem(control, item) {
    control._listModel.append(_normalizeItem(item))
}

function addItems(control, items) {
    var safeItems = items && typeof items.length === "number" ? items : []
    for (var i = 0; i < safeItems.length; i++) addItem(control, safeItems[i])
}

function insertItem(control, row, item) {
    var listModel = control._listModel
    if (row < 0) row = 0
    if (row > listModel.count) row = listModel.count
    listModel.insert(row, _normalizeItem(item))
}

function insertItems(control, row, items) {
    var safeItems = items && typeof items.length === "number" ? items : []
    for (var i = 0; i < safeItems.length; i++) {
        insertItem(control, row + i, safeItems[i])
    }
}

function takeItem(control, row) {
    var listModel = control._listModel
    if (row < 0 || row >= listModel.count) return null
    var item = _getItemObject(control, row)
    listModel.remove(row)
    updateSelectedRows(control)
    return item
}

function item(control, row) {
    return row < 0 || row >= control._listModel.count
        ? null : _getItemObject(control, row)
}

function row(control, itemValue) {
    var searchText = typeof itemValue === "string"
                     ? itemValue : (itemValue ? (itemValue.text || "") : "")
    var listModel = control._listModel
    for (var i = 0; i < listModel.count; i++) {
        if (listModel.get(i).text === searchText) return i
    }
    return -1
}

function currentItem(control) {
    return item(control, control.currentIndex)
}

function setCurrentItem(control, itemValue, command) {
    var currentRow = row(control, itemValue)
    if (currentRow >= 0) setCurrentRow(control, currentRow, command)
}

function currentRow(control) {
    return control.currentIndex
}

function setCurrentRow(control, rowValue, command) {
    var listModel = control._listModel
    if (rowValue >= 0 && rowValue < listModel.count) {
        control.currentIndex = rowValue
        if (control.selectionMode !== control.noSelection) {
            control._selectedRows = [rowValue]
            control.itemSelectionChanged()
        }
    }
}

function selectedItems(control) {
    var result = []
    for (var i = 0; i < control._selectedRows.length; i++) {
        var itemValue = item(control, control._selectedRows[i])
        if (itemValue) result.push(itemValue)
    }
    return result
}

function clearSelection(control) {
    control._selectedRows = []
    control.currentIndex = -1
    control.itemSelectionChanged()
}

function selectAll(control) {
    if (control.selectionMode === control.noSelection
            || control.selectionMode === control.singleSelection) return
    control._selectedRows = []
    for (var i = 0; i < control._listModel.count; i++) {
        control._selectedRows.push(i)
    }
    control.itemSelectionChanged()
}

function setSelectionMode(control, mode) {
    control.selectionMode = mode
    if (mode === control.singleSelection && control._selectedRows.length > 1) {
        control._selectedRows = control.currentIndex >= 0
                                 ? [control.currentIndex] : []
    }
}

function findItems(control, text, flags) {
    var result = []
    var pattern = text.toLowerCase()
    var listModel = control._listModel
    for (var i = 0; i < listModel.count; i++) {
        var itemText = (listModel.get(i).text || "").toLowerCase()
        var match = false
        if (flags === 0) match = itemText === pattern
        else if (flags === 1) match = itemText.indexOf(pattern) >= 0
        else if (flags === 2) match = itemText.startsWith(pattern)
        else if (flags === 3) match = itemText.endsWith(pattern)
        else if (flags === 4) match = new RegExp(text).test(itemText)
        if (match) result.push(_getItemObject(control, i))
    }
    return result
}

function sortItems(control, order) {
    var listModel = control._listModel
    var sortedRows = []
    var currentOrder = []
    var currentOriginalIndex = control.currentIndex
    var selectedOriginalRows = control._selectedRows.slice()
    for (var i = 0; i < listModel.count; i++) {
        sortedRows.push({
            originalIndex: i,
            text: String(listModel.get(i).text || "")
        })
        currentOrder.push(i)
    }
    sortedRows.sort(function(left, right) {
        var comparison = left.text.localeCompare(right.text)
        return order === 1 ? -comparison : comparison
    })
    for (var target = 0; target < sortedRows.length; target++) {
        var source = currentOrder.indexOf(sortedRows[target].originalIndex)
        if (source === target) continue
        listModel.move(source, target, 1)
        var moved = currentOrder.splice(source, 1)[0]
        currentOrder.splice(target, 0, moved)
    }
    control.currentIndex = currentOrder.indexOf(currentOriginalIndex)
    control._selectedRows = selectedOriginalRows.map(function(rowValue) {
        return currentOrder.indexOf(rowValue)
    }).filter(function(rowValue) {
        return rowValue >= 0
    })
}

function clear(control) {
    control._listModel.clear()
    control._selectedRows = []
    control.currentIndex = -1
}

function setItemText(control, row, text) {
    if (row >= 0 && row < control._listModel.count) {
        control._listModel.setProperty(row, "text", text)
    }
}

function setItemIcon(control, row, icon) {
    if (row >= 0 && row < control._listModel.count) {
        control._listModel.setProperty(row, "icon", icon)
    }
}

function setItemData(control, row, role, value) {
    if (row >= 0 && row < control._listModel.count) {
        var data = control._listModel.get(row).data || {}
        data[role] = value
        control._listModel.setProperty(row, "data", data)
    }
}

function itemData(control, row, role) {
    if (row < 0 || row >= control._listModel.count) return undefined
    var data = control._listModel.get(row).data
    return data ? data[role] : undefined
}

function setItemCheckState(control, row, state) {
    if (row >= 0 && row < control._listModel.count) {
        control._listModel.setProperty(row, "checkState", state)
    }
}

function itemCheckState(control, row) {
    if (row < 0 || row >= control._listModel.count) return 0
    return control._listModel.get(row).checkState || 0
}

function setItemSelected(control, row, selected) {
    if (row < 0 || row >= control._listModel.count) return
    control._listModel.setProperty(row, "selected", selected)
    var index = control._selectedRows.indexOf(row)
    if (selected && index < 0) {
        control._selectedRows.push(row)
    } else if (!selected && index >= 0) {
        control._selectedRows.splice(index, 1)
    }
    control._selectedRows = control._selectedRows.slice()
}

function updateSelectedRows(control) {
    control._selectedRows = control._selectedRows.filter(function(rowValue) {
        return rowValue < control._listModel.count
    })
}

function handleItemClick(control, row, button, modifiers, qt) {
    if (control.selectionMode === control.noSelection) return
    if (button === qt.RightButton && !control.selectOnRightClick) return

    if (control.selectionMode === control.singleSelection) {
        control.currentIndex = row
        control._selectedRows = [row]
    } else if (control.selectionMode === control.multiSelection) {
        var index = control._selectedRows.indexOf(row)
        if (index >= 0) control._selectedRows.splice(index, 1)
        else control._selectedRows.push(row)
        control._selectedRows = control._selectedRows.slice()
        control.currentIndex = row
    } else if (control.selectionMode === control.extendedSelection) {
        if (modifiers & qt.ControlModifier) {
            var controlIndex = control._selectedRows.indexOf(row)
            if (controlIndex >= 0) control._selectedRows.splice(controlIndex, 1)
            else control._selectedRows.push(row)
            control._selectedRows = control._selectedRows.slice()
        } else if (modifiers & qt.ShiftModifier && control.currentIndex >= 0) {
            var start = Math.min(control.currentIndex, row)
            var end = Math.max(control.currentIndex, row)
            control._selectedRows = []
            for (var i = start; i <= end; i++) control._selectedRows.push(i)
        } else {
            control._selectedRows = [row]
        }
        control.currentIndex = row
    }
    control._pressedRow = -1
    control.itemSelectionChanged()
}
