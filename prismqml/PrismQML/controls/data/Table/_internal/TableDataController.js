// TableDataController - Table JS data mutation helpers 表格 JS 数据变更辅助
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function _isPureJsArray(table) {
    return Array.isArray(table.tableData)
}

function _captureCellWidgetEntries(table, data) {
    var entries = []
    var keys = Object.keys(table.cellWidgets)
    for (var index = 0; index < keys.length; index++) {
        var separator = keys[index].indexOf("_")
        var row = parseInt(keys[index].slice(0, separator))
        var column = parseInt(keys[index].slice(separator + 1))
        if (row >= 0 && row < data.length) {
            entries.push({
                "rowData": data[row],
                "column": column,
                "widget": table.cellWidgets[keys[index]]
            })
        }
    }
    return entries
}

function _restoreCellWidgets(table, entries, data) {
    var nextWidgets = {}
    for (var index = 0; index < entries.length; index++) {
        var row = data.indexOf(entries[index].rowData)
        if (row >= 0)
            nextWidgets[row + "_" + entries[index].column] = entries[index].widget
    }
    table.cellWidgets = nextWidgets
}

function _rowRefs(indices, data) {
    var refs = []
    for (var index = 0; index < indices.length; index++) {
        if (indices[index] >= 0 && indices[index] < data.length)
            refs.push(data[indices[index]])
    }
    return refs
}

function _rowIndices(refs, data) {
    var indices = []
    for (var index = 0; index < refs.length; index++) {
        var row = data.indexOf(refs[index])
        if (row >= 0) indices.push(row)
    }
    return indices
}

function addRow(table, data) {
    if (!_isPureJsArray(table)) {
        console.warn("TableWidget: Cannot addRow via JS when a QAbstractListModel is bound.")
        return
    }
    table.tableData = table.tableData.concat([data])
}

function clearData(table) {
    if (!_isPureJsArray(table)) {
        console.warn("TableWidget: Cannot clearData via JS when a QAbstractListModel is bound.")
        return
    }
    table.tableData = []
    table.selectedRows = []
    table.currentRow = -1
    table.currentColumn = -1
    table.cellWidgets = ({})
}

function removeRow(table, rowIndex) {
    if (!_isPureJsArray(table)) {
        console.warn("TableWidget: Cannot removeRow via JS when a QAbstractListModel is bound.")
        return
    }
    if (rowIndex < 0 || rowIndex >= table.tableData.length) return
    var data = table.tableData.slice()
    var currentValid = table.currentRow >= 0 && table.currentRow < data.length
    var currentRef = currentValid ? data[table.currentRow] : null
    var selectedRefs = _rowRefs(table.selectedRows, data)
    var widgetEntries = _captureCellWidgetEntries(table, data)
    data.splice(rowIndex, 1)
    table.tableData = data
    table.currentRow = currentValid ? data.indexOf(currentRef) : -1
    if (table.currentRow < 0) table.currentColumn = -1
    table.selectedRows = _rowIndices(selectedRefs, data)
    _restoreCellWidgets(table, widgetEntries, data)
}

function getRow(table, rowIndex) {
    if (!_isPureJsArray(table)) return null
    return rowIndex >= 0 && rowIndex < table.tableData.length
        ? table.tableData[rowIndex] : null
}

function setRowCount(table, count) {
    if (!_isPureJsArray(table)) {
        console.warn("TableWidget: Cannot setRowCount via JS when a QAbstractListModel is bound.")
        return
    }
    var targetCount = Number(count)
    if (!isFinite(targetCount) || targetCount < 0) targetCount = 0
    targetCount = Math.floor(targetCount)
    var data = table.tableData.slice()
    var currentValid = table.currentRow >= 0 && table.currentRow < data.length
    var currentRef = currentValid ? data[table.currentRow] : null
    var selectedRefs = _rowRefs(table.selectedRows, data)
    var widgetEntries = _captureCellWidgetEntries(table, data)
    while (data.length < targetCount) data.push({})
    while (data.length > targetCount) data.pop()
    table.tableData = data
    table.currentRow = currentValid ? data.indexOf(currentRef) : -1
    if (table.currentRow < 0) table.currentColumn = -1
    table.selectedRows = _rowIndices(selectedRefs, data)
    _restoreCellWidgets(table, widgetEntries, data)
}

function setColumnCount(table, count) {
    var columns = (table._safeColumns || []).slice()
    while (columns.length < count) {
        columns.push({ "text": "", "width": 0.15, "role": "col" + columns.length })
    }
    while (columns.length > count) columns.pop()
    table.columns = columns
}

function setHorizontalHeaderLabels(table, labels) {
    var columns = []
    var safeLabels = table._listOrEmpty(labels)
    if (safeLabels.length === 0) {
        table.columns = []
        return
    }
    for (var index = 0; index < safeLabels.length; index++) {
        columns.push({
            "text": safeLabels[index],
            "width": 1.0 / safeLabels.length,
            "role": "col" + index
        })
    }
    table.columns = columns
}

function setItem(table, row, column, value) {
    if (!_isPureJsArray(table)) {
        console.warn("TableWidget: Cannot setItem via JS when a QAbstractListModel is bound.")
        return
    }
    var safeColumns = table._safeColumns || []
    if (row < 0 || row >= table.tableData.length
            || column < 0 || column >= safeColumns.length) return
    var data = table.tableData.slice()
    var rowData = Object.assign({}, data[row])
    var columnData = safeColumns[column] || {}
    rowData[columnData.role] = typeof value === "string"
        ? value : (value && value.text || value)
    data[row] = rowData
    table.tableData = data
}

function item(table, row, column) {
    var safeColumns = table._safeColumns || []
    if (!_isPureJsArray(table)) return null
    if (row < 0 || row >= table.tableData.length
            || column < 0 || column >= safeColumns.length) return null
    var columnData = safeColumns[column] || {}
    var rowData = table.tableData[row] || {}
    var value = rowData[columnData.role]
    return {
        "text": value === null || value === undefined ? "" : value,
        "row": row,
        "column": column
    }
}

function selectedItems(table) {
    var result = []
    for (var index = 0; index < table.selectedRows.length; index++) {
        var row = table.selectedRows[index]
        for (var column = 0; column < (table._safeColumns || []).length; column++)
            result.push(item(table, row, column))
    }
    return result
}

function sortItems(table, column, order) {
    var safeColumns = table._safeColumns || []
    if (column < 0 || column >= safeColumns.length) return
    if (!_isPureJsArray(table)) {
        console.warn("TableWidget: Cannot sortItems via JS when a QAbstractListModel is bound.")
        return
    }
    var role = (safeColumns[column] || {}).role
    var data = table.tableData.slice()
    var currentValid = table.currentRow >= 0 && table.currentRow < data.length
    var currentRef = currentValid ? data[table.currentRow] : null
    var selectedRefs = _rowRefs(table.selectedRows, data)
    var widgetEntries = _captureCellWidgetEntries(table, data)
    data.sort(function(left, right) {
        var leftValue = (left || {})[role]
        var rightValue = (right || {})[role]
        var leftText = String(
            leftValue === null || leftValue === undefined ? "" : leftValue
        )
        var rightText = String(
            rightValue === null || rightValue === undefined ? "" : rightValue
        )
        var comparison = leftText.localeCompare(rightText)
        return order === 1 ? -comparison : comparison
    })
    table.tableData = data
    table.currentRow = currentValid ? data.indexOf(currentRef) : -1
    table.selectedRows = _rowIndices(selectedRefs, data)
    _restoreCellWidgets(table, widgetEntries, data)
}

function setData(table, data, headers) {
    if (headers) setHorizontalHeaderLabels(table, headers)
    if (!data || !data.length) {
        table.tableData = []
        return
    }
    var safeColumns = table._safeColumns || []
    var columns = safeColumns.length > 0 ? safeColumns.slice() : []
    if (columns.length === 0 && data[0]) {
        var columnCount = Array.isArray(data[0])
            ? data[0].length : Object.keys(data[0]).length
        for (var column = 0; column < columnCount; column++) {
            columns.push({
                "text": table._columnLabel(column + 1),
                "width": 1.0 / columnCount,
                "role": "col" + column
            })
        }
        table.columns = columns
    }
    var result = []
    for (var row = 0; row < data.length; row++) {
        var rowObject = {}
        if (Array.isArray(data[row])) {
            for (var index = 0;
                    index < data[row].length && index < columns.length;
                    index++) {
                rowObject[columns[index].role] = data[row][index]
            }
        } else {
            rowObject = data[row]
        }
        result.push(rowObject)
    }
    table.tableData = result
}

function setCellWidget(table, row, column, widget) {
    if (!widget) return
    var key = row + "_" + column
    var widgets = Object.assign({}, table.cellWidgets)
    widgets[key] = widget
    table.cellWidgets = widgets
}

function cellWidget(table, row, column) {
    return table.cellWidgets[row + "_" + column] || null
}

function hasCellWidget(table, row, column) {
    return table.cellWidgets.hasOwnProperty(row + "_" + column)
}
