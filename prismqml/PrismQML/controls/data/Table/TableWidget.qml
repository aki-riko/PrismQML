// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import ".."
import "../../menus/"
import "../../navigation/"
import "_internal" as TableInternal
import "_internal/TableDataController.js" as TableDataController
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// TableWidget - Fluent style table widget 表格控件
// High performance with direct array model 使用直接数组模型的高性能实现
// QTableWidget API compatible QTableWidget API兼容
DataWidgetCore {
    id: root

    // ==================== Public Props 公开属性 ====================
    property var tableData: []  // Direct array model for performance 直接数组模型提升性能
    property var columns: []  // [{text, width, role}]

    // 集中渲染模式 (Phase 4 100B 优化): true 时 delegate 用 PaintedRow,
    // 整行收敛到 1 个 Canvas paint(),quasi-90% 减少 QObject 开销。
    // 触发条件:
    // - 行数 >= 100k 且 delegate 子树 > 5 个 QObject 时强烈推荐
    // - 业务 delegate 不需要每 cell 单独 hover/click 时强烈推荐
    // 限制:
    // - 单 cell hover 反馈消失 (整行 hover 仍可)
    // - 内嵌 widget (CheckBox/ProgressBar 等) 无法在 paint 里渲染,需自定义 paintCallback
    property bool paintedRowMode: false
    // paintedRowMode=true 时由调用方提供自定义绘制逻辑 (例如绘制 income/expense 的小图标)
    // 接口: function(ctx, columns, rowData, width, height) -> void
    property var paintedRowExtra: null

    // Selection 选择
    property int currentRow: -1
    property int currentColumn: -1
    property var selectedRows: []
    property bool selectOnRightClick: false
    property color checkedColor: Enums.accentColor
    property color checkedColorDark: Enums.accentColor

    // Appearance 外观
    property bool showGrid: false
    property bool alternatingRowColors: true
    property bool sortingEnabled: false
    property bool borderVisible: true

    // Edit 编辑
    property bool editable: false

    // Pagination 分页
    property bool showPagination: false
    property int currentPage: 1
    property int totalPages: 1
    property int visiblePages: 5

    // Computed values 计算值
    // 必须用普通 property + Connections 显式跟踪 model.modelReset/rowsInserted/rowsRemoved,
    // 因为 QAbstractListModel.rowCount() 是函数调用,QML binding 不会自动 invalidate
    property int rowCount: _calcRowCount()
    readonly property int columnCount: (_safeColumns || []).length
    readonly property real _columnViewportWidth: listView.width > 0 ? listView.width : root.width
    readonly property Component _paintedRowComponent: contentLayer.paintedRowComponent

    // Context menu 右键菜单
    property bool contextMenuEnabled: false
    property bool defaultContextMenuEnabled: false // System default context menu 系统自带默认上下文菜单

    // Cell widgets 单元格控件存储 {"row_col": QQuickItem}
    property var cellWidgets: ({})

    // Column-width single source of truth 列宽单一真相源
    // 每列实际像素宽度数组, 跟 columns 索引对齐。
    // 计算规则 (按优先级):
    //   1) column.autoWidth === true 且提供 measureWidth(rowData) → 扫前 N 行取 max,
    //      clamp 到 [minWidth, maxWidth]
    //   2) 否则按 column.width: < 1 视为内部视口宽度比例, >= 1 视为绝对像素
    //   3) column.width 缺省时 fallback 0.15
    // delegate / cellItem / contentTotalWidth / dblclick hit-test 全部从这里取,
    // 不再各自重算 (避免漂移)。
    property var _columnPixelWidths: []
    readonly property var _safeColumns:
        columns === null || columns === undefined ? []
        : (typeof columns.length === "number" ? columns : [])

    // ==================== Signals 信号 ====================
    signal pageChanged(int page)
    signal rowClicked(int index, var rowData)
    signal rowDoubleClicked(int index, var rowData)
    signal cellClicked(int row, int column)
    signal cellDoubleClicked(int row, int column)
    signal currentCellChanged(int currentRow, int currentColumn, int previousRow, int previousColumn)
    signal itemSelectionChanged()
    signal customContextMenuRequested(point pos)  // 右键菜单信号 Context menu signal

    // ==================== Internal Methods 内部方法 ====================
    function _listOrEmpty(value) {
        return value && typeof value.length === "number" ? value : []
    }

    function _calcRowCount() {
        if (!tableData) return 0
        // PySide6 把 list[dict] 转 QVariantList 给 QML, QVariantList 不是 JS Array
        // (Array.isArray 返回 false), 但有 length 属性。先按 length 判, 再 fallback。
        if (typeof tableData.length === 'number') return tableData.length
        if (typeof tableData.rowCount === 'function') return tableData.rowCount()
        if (tableData.count !== undefined) return tableData.count
        return 0
    }

    function _recomputeColumnWidths() {
        var safeColumns = _safeColumns || []
        var widths = []
        for (var i = 0; i < safeColumns.length; i++) {
            widths.push(_computeColumnWidth(safeColumns[i]))
        }
        // 自适应列宽 (autoWidth) 算完后, 如果总宽 < 表格容器宽, 按比例放大到铺满,
        // 避免出现"右侧大片空白"的视觉缺陷。
        // 如果总宽 > 容器宽, 保持原值, DataWidgetCore 会启用横向滚动。
        // 只在所有列都没显式 width (即都是 autoWidth) 时拉伸, 业务设了固定 width 的列尊重原值。
        var allAuto = safeColumns.length > 0
        for (var k = 0; k < safeColumns.length; k++) {
            var c = safeColumns[k] || {}
            var explicitWidth = (c.autoWidth === false) || (c.width !== undefined && c.width !== null)
            if (explicitWidth) { allAuto = false; break }
        }
        if (allAuto && root.width > 0) {
            var sum = 0
            for (var s = 0; s < widths.length; s++) sum += widths[s]
            var avail = root._columnViewportWidth
            if (sum > 0 && sum < avail) {
                var scale = avail / sum
                for (var t = 0; t < widths.length; t++) widths[t] = Math.floor(widths[t] * scale)
            }
        }
        _columnPixelWidths = widths
    }

    // 默认 measureWidth: 取 rowData[role] 转字符串, 按字符宽度估算
    // 中文(Unicode > 127) 14px, 英文/数字 8px, 不含 padding (引擎层 cellPadding 统一加)。
    // 业务不显式提供 measureWidth 时, 所有列自动按内容自适应。
    function _defaultMeasureWidth(role) {
        return function(rowData) {
            if (!rowData) return 0
            var v = rowData[role]
            if (v === undefined || v === null) return 0
            // 数组类型 (例如 income/expense [{amount, kind}, ...]): 按 JSON 字符长度估算
            // 这只是兜底, 业务通常会显式给货币列写 measureWidth
            var s = (typeof v === 'object') ? JSON.stringify(v) : String(v)
            var w = 0
            for (var k = 0; k < s.length; k++) {
                var ch = s.charCodeAt(k)
                w += ch > 127 ? 14 : 8
            }
            return w
        }
    }

    function _computeColumnWidth(col) {
        if (!col) col = {}
        // autoWidth 决策:
        // - 业务显式 col.autoWidth = true/false → 走业务设置
        // - 否则: 没写 width 就默认 autoWidth (引擎按内容自适应);
        //         写了 width 尊重业务 (老代码不破坏视觉)
        var autoOn
        if (typeof col.autoWidth === 'boolean') {
            autoOn = col.autoWidth
        } else {
            autoOn = (col.width === undefined || col.width === null)
        }
        if (autoOn) {
            var measure = (typeof col.measureWidth === 'function')
                          ? col.measureWidth
                          : _defaultMeasureWidth(col.role)
            var sampleSize = col.widthSampleSize || 100
            var minW = col.minWidth || 60
            var maxW = col.maxWidth || 600
            // autoWidth 列默认两侧合计 32px padding (左右各 16, 跟主流表格库一致)
            // 防止内容贴边视觉缺陷, 业务可显式 col.cellPadding = N 覆盖
            var pad = (typeof col.cellPadding === 'number') ? col.cellPadding : 32
            var n = Math.min(sampleSize, _rowCountForMeasure())
            // 算表头文字本身宽度作为最小基线 (列名比内容长时不至于截断)
            var headerText = String(col.text || "")
            var headerW = 0
            for (var hi = 0; hi < headerText.length; hi++) {
                var hc = headerText.charCodeAt(hi)
                headerW += hc > 127 ? 14 : 8
            }
            var max = Math.max(0, headerW)
            for (var r = 0; r < n; r++) {
                var rowData = _getRowForMeasure(r)
                if (!rowData) continue
                try {
                    var px = measure(rowData)
                    if (typeof px === 'number' && px > max) max = px
                } catch (e) {
                    console.warn("TableWidget._computeColumnWidth: measureWidth threw:", e)
                }
            }
            // 加 padding 后再 clamp, 避免短内容列下溢到 minW 之下
            return Math.max(minW, Math.min(max + pad, maxW))
        }
        // 静态宽度: < 1 比例, >= 1 像素, 缺省 0.15
        var w = col.width || 0.15
        return w < 1 ? root._columnViewportWidth * w : w
    }

    function _rowCountForMeasure() {
        if (!tableData) return 0
        if (typeof tableData.length === 'number') return tableData.length
        // SqlListModel 提供 count() slot, 比直接调 rowCount(QModelIndex) 在 QML 端更稳
        if (typeof tableData.count === 'function') {
            try { return tableData.count() } catch (e) {}
        }
        if (typeof tableData.rowCount === 'function') {
            try { return tableData.rowCount() } catch (e) {}
        }
        // 最后 fallback: 走基类 DataWidgetCore 的 rowCount property
        if (typeof root.rowCount === 'number' && root.rowCount > 0) return root.rowCount
        return 0
    }

    function _getRowForMeasure(idx) {
        if (!tableData) return null
        if (typeof tableData.length === 'number') return tableData[idx]
        if (typeof tableData.getRow === 'function') return tableData.getRow(idx)
        return null
    }

    // Selection and row identity helpers 选择与行身份辅助方法
    function _isRowSelected(row) {
        return selectedRows.indexOf(row) >= 0
    }

    function _selectRow(row) {
        var prevRow = currentRow
        currentRow = row
        selectedRows = [row]
        if (prevRow !== row) {
            currentCellChanged(row, 0, prevRow, 0)
        }
        itemSelectionChanged()
    }

    // ==================== Data API 数据 API ====================
    // Keep the public surface on TableWidget while delegating data state.
    // 保留 TableWidget 公开面，同时委托数据状态处理。
    function _isPureJsArray() { return TableDataController._isPureJsArray(root) }

    function addRow(data) { TableDataController.addRow(root, data) }

    function clearData() { TableDataController.clearData(root) }

    function removeRow(index) { TableDataController.removeRow(root, index) }

    function getRow(index) { return TableDataController.getRow(root, index) }

    function setRowCount(count) { TableDataController.setRowCount(root, count) }

    function setColumnCount(count) { TableDataController.setColumnCount(root, count) }

    function setHorizontalHeaderLabels(labels) {
        TableDataController.setHorizontalHeaderLabels(root, labels)
    }

    function setItem(row, column, value) {
        TableDataController.setItem(root, row, column, value)
    }

    function item(row, column) { return TableDataController.item(root, row, column) }

    function selectedItems() { return TableDataController.selectedItems(root) }

    function clearSelection() {
        selectedRows = []
        currentRow = -1
        currentColumn = -1
        itemSelectionChanged()
    }

    function selectRow(row) {
        if (row >= 0 && row < rowCount) {
            _selectRow(row)
        }
    }

    function setCurrentCell(row, column) {
        if (row >= 0 && row < rowCount) {
            _selectRow(row)
            currentColumn = column
        }
    }

    function currentItem() { return item(currentRow, currentColumn >= 0 ? currentColumn : 0) }

    // ==================== Sorting API 排序 API ====================
    function sortItems(column, order) {
        TableDataController.sortItems(root, column, order)
    }

    // Scroll API 滚动 API
    function scrollToTop() { listView.positionViewAtBeginning() }
    function scrollToBottom() { listView.positionViewAtEnd() }
    function scrollToRow(row) {
        if (row >= 0 && row < rowCount)
            listView.positionViewAtIndex(row, ListView.Center)
    }

    // setData convenience API setData 便捷 API
    function setData(data, headers) {
        TableDataController.setData(root, data, headers)
    }

    // Cell widget support 单元格控件支持
    function setCellWidget(row, column, widget) {
        TableDataController.setCellWidget(root, row, column, widget)
    }

    function cellWidget(row, column) {
        return TableDataController.cellWidget(root, row, column)
    }

    function hasCellWidget(row, column) {
        return TableDataController.hasCellWidget(root, row, column)
    }

    function _showDefaultContextMenu(rowIndex, x, y) {
        var menu = contentLayer.defaultTableContextMenuLoader.item
        if (menu) menu.showMenu(rowIndex, x, y)
    }

    function _columnLabel(index) {
        return Translator.tr("column").replace("{index}", index)
    }

    // ==================== Size 尺寸 ====================
    // Base configuration 基类配置
    itemCount: rowCount
    listModel: tableData
    showHeader: (_safeColumns || []).length > 0

    // 计算所有列的总像素宽度 (基类 DataWidgetCore 据此判断是否启用横向滚动)。
    contentTotalWidth: {
        var total = 0
        for (var i = 0; i < _columnPixelWidths.length; i++) {
            total += _columnPixelWidths[i] || 0
        }
        return total
    }

    // 触发条件: columns 数组变 / 数据变 / root 宽度变
    onColumnsChanged: _recomputeColumnWidths()
    onWidthChanged: _recomputeColumnWidths()
    onTableDataChanged: { rowCount = _calcRowCount(); _recomputeColumnWidths() }
    onListModelChanged: _recomputeColumnWidths()

    // Layout override 覆盖内置布局
    // Adjust flickable bottom margin when pagination is shown 当显示分页时，调整滚动区域的底部边距以免被遮挡
    Component.onCompleted: {
        _recomputeColumnWidths()
        if (root.showPagination && typeof listView !== 'undefined') {
            listView.bottomMargin = 50 // Reserve space for pager 为底部分页器预留空间
        }

        // Ensure property exists before watching 确保listView存在再监控
        if (typeof listView !== 'undefined') {
            root.showPaginationChanged.connect(function() {
                listView.bottomMargin = root.showPagination ? 50 : 0
            })
        }
    }

    contentDelegate: contentLayer.contentDelegate
    headerContent: contentLayer.headerContent

    // ==================== Content 内容 ====================
    TableInternal.TableWidgetContent {
        id: contentLayer
        table: root
    }
}
