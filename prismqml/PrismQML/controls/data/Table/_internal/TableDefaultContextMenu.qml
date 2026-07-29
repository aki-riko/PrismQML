// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../menus/"

// TableDefaultContextMenu - Built-in row actions 内置表格行操作菜单
ContextMenu {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var table: null

    // ==================== Internal Props 内部属性 ====================
    property int activeRowIndex: -1

    // ==================== Public Methods 公开方法 ====================
    function showMenu(rowIndex, x, y) {
        if (!control.table) return
        activeRowIndex = rowIndex
        popup(x, y, control.table)
    }

    autoBindRightClick: false

    Action {
        text: { Translator._v; return Translator.tr("copy_selected_row") }
        icon: "Copy"
        onTriggered: {
            if (!control.table || control.activeRowIndex < 0) return
            var rowData = control.table.getRow(control.activeRowIndex)
            if (!rowData) return
            var textParts = []
            for (var i = 0; i < (control.table._safeColumns || []).length; i++) {
                var columnData = control.table._safeColumns[i] || {}
                textParts.push(rowData[columnData.role] || "")
            }
            ClipboardHelper.copy(textParts.join("\t"))
        }
    }

    MenuSeparator {}

    Action {
        text: { Translator._v; return Translator.tr("insert_row_above") }
        icon: "Add"
        onTriggered: {
            if (!control.table || control.activeRowIndex < 0) return
            if (!control.table._isPureJsArray()) {
                console.warn("TableWidget: Cannot insert row via built-in menu when a QAbstractListModel is bound.")
                return
            }
            var rows = control.table.tableData.slice()
            rows.splice(control.activeRowIndex, 0, {})
            control.table.tableData = rows
        }
    }

    Action {
        text: { Translator._v; return Translator.tr("insert_row_below") }
        icon: "Add"
        onTriggered: {
            if (!control.table || control.activeRowIndex < 0) return
            if (!control.table._isPureJsArray()) {
                console.warn("TableWidget: Cannot insert row via built-in menu when a QAbstractListModel is bound.")
                return
            }
            var rows = control.table.tableData.slice()
            rows.splice(control.activeRowIndex + 1, 0, {})
            control.table.tableData = rows
        }
    }

    MenuSeparator {}

    Action {
        text: { Translator._v; return Translator.tr("delete_selected_row") }
        icon: "Delete"
        onTriggered: {
            if (control.table && control.activeRowIndex >= 0) {
                control.table.removeRow(control.activeRowIndex)
            }
        }
    }
}
