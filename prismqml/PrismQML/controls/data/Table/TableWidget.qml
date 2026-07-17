// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import ".."
import "../../menus/"
import "../../navigation/"
import "_internal" as TableInternal
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
    readonly property int columnCount: columns.length

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
    //   2) 否则按 column.width: < 1 视为 root.width 比例, >= 1 视为绝对像素
    //   3) column.width 缺省时 fallback 0.15
    // delegate / cellItem / contentTotalWidth / dblclick hit-test 全部从这里取,
    // 不再各自重算 (避免漂移)。
    property var _columnPixelWidths: []

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
        var widths = []
        for (var i = 0; i < columns.length; i++) {
            widths.push(_computeColumnWidth(columns[i]))
        }
        // 自适应列宽 (autoWidth) 算完后, 如果总宽 < 表格容器宽, 按比例放大到铺满,
        // 避免出现"右侧大片空白"的视觉缺陷。
        // 如果总宽 > 容器宽, 保持原值, DataWidgetCore 会启用横向滚动。
        // 只在所有列都没显式 width (即都是 autoWidth) 时拉伸, 业务设了固定 width 的列尊重原值。
        var allAuto = columns.length > 0
        for (var k = 0; k < columns.length; k++) {
            var c = columns[k]
            var explicitWidth = (c.autoWidth === false) || (c.width !== undefined && c.width !== null)
            if (explicitWidth) { allAuto = false; break }
        }
        if (allAuto && root.width > 0) {
            var sum = 0
            for (var s = 0; s < widths.length; s++) sum += widths[s]
            // 给 listView 自身的 contentMargin / scrollbar 等留 ~20px 余量
            var avail = root.width - 20
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
        return w < 1 ? root.width * w : w
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

    function _captureCellWidgetEntries(data) {
        var entries = []
        var keys = Object.keys(cellWidgets)
        for (var i = 0; i < keys.length; i++) {
            var separator = keys[i].indexOf("_")
            var row = parseInt(keys[i].slice(0, separator))
            var column = parseInt(keys[i].slice(separator + 1))
            if (row >= 0 && row < data.length) {
                entries.push({ rowData: data[row], column: column, widget: cellWidgets[keys[i]] })
            }
        }
        return entries
    }

    function _restoreCellWidgets(entries, data) {
        var nextWidgets = {}
        for (var i = 0; i < entries.length; i++) {
            var row = data.indexOf(entries[i].rowData)
            if (row >= 0) nextWidgets[row + "_" + entries[i].column] = entries[i].widget
        }
        cellWidgets = nextWidgets
    }

    function _rowRefs(indices, data) {
        var refs = []
        for (var i = 0; i < indices.length; i++) {
            if (indices[i] >= 0 && indices[i] < data.length) refs.push(data[indices[i]])
        }
        return refs
    }

    function _rowIndices(refs, data) {
        var indices = []
        for (var i = 0; i < refs.length; i++) {
            var row = data.indexOf(refs[i])
            if (row >= 0) indices.push(row)
        }
        return indices
    }

    // ==================== Public Methods 公开方法 ====================
    // Data API 数据 API
    // Note: To use these JS modifying methods, tableData MUST be a pure Javascript Array. 注意：若使用这些 JS 操作方法，tableData 必须保证是纯 JavaScript 数组。
    // If a QAbstractListModel is bound, you should perform modifications at Python side! 如果绑定了 C++ ListModel，应该在 Python 后端进行这些修改！
    function _isPureJsArray() { return Array.isArray(tableData) }

    function addRow(data) {
        if (!_isPureJsArray()) { console.warn("TableWidget: Cannot addRow via JS when a QAbstractListModel is bound."); return }
        tableData = tableData.concat([data])
    }

    function clearData() {
        if (!_isPureJsArray()) { console.warn("TableWidget: Cannot clearData via JS when a QAbstractListModel is bound."); return }
        tableData = []
        selectedRows = []
        currentRow = -1
        currentColumn = -1
        cellWidgets = ({})
    }

    function removeRow(idx) {
        if (!_isPureJsArray()) { console.warn("TableWidget: Cannot removeRow via JS when a QAbstractListModel is bound."); return }
        if (idx >= 0 && idx < tableData.length) {
            var arr = tableData.slice()
            var currentValid = currentRow >= 0 && currentRow < arr.length
            var currentRef = currentValid ? arr[currentRow] : null
            var selectedRefs = _rowRefs(selectedRows, arr)
            var widgetEntries = _captureCellWidgetEntries(arr)
            arr.splice(idx, 1)
            tableData = arr
            currentRow = currentValid ? arr.indexOf(currentRef) : -1
            if (currentRow < 0) currentColumn = -1
            selectedRows = _rowIndices(selectedRefs, arr)
            _restoreCellWidgets(widgetEntries, arr)
        }
    }

    function getRow(idx) {
        if (!_isPureJsArray()) return null; // Model data should be fetched from Python side.
        return idx >= 0 && idx < tableData.length ? tableData[idx] : null
    }

    function setRowCount(count) {
        if (!_isPureJsArray()) { console.warn("TableWidget: Cannot setRowCount via JS when a QAbstractListModel is bound."); return }
        var targetCount = Number(count)
        if (!isFinite(targetCount) || targetCount < 0) targetCount = 0
        targetCount = Math.floor(targetCount)
        var arr = tableData.slice()
        var currentValid = currentRow >= 0 && currentRow < arr.length
        var currentRef = currentValid ? arr[currentRow] : null
        var selectedRefs = _rowRefs(selectedRows, arr)
        var widgetEntries = _captureCellWidgetEntries(arr)
        while (arr.length < targetCount) arr.push({})
        while (arr.length > targetCount) arr.pop()
        tableData = arr
        currentRow = currentValid ? arr.indexOf(currentRef) : -1
        if (currentRow < 0) currentColumn = -1
        selectedRows = _rowIndices(selectedRefs, arr)
        _restoreCellWidgets(widgetEntries, arr)
    }

    function setColumnCount(count) {
        // Columns are defined via columns property 列通过columns属性定义
        var cols = columns.slice()
        while (cols.length < count) cols.push({ text: "", width: 0.15, role: "col" + cols.length })
        while (cols.length > count) cols.pop()
        columns = cols
    }

    function setHorizontalHeaderLabels(labels) {
        var cols = []
        for (var i = 0; i < labels.length; i++) {
            cols.push({ text: labels[i], width: 1.0 / labels.length, role: "col" + i })
        }
        columns = cols
    }

    function setItem(row, column, value) {
        if (!_isPureJsArray()) { console.warn("TableWidget: Cannot setItem via JS when a QAbstractListModel is bound."); return }
        if (row >= 0 && row < tableData.length && column >= 0 && column < columns.length) {
            var arr = tableData.slice()
            var rowData = Object.assign({}, arr[row])
            rowData[columns[column].role] = typeof value === "string" ? value : (value.text || value)
            arr[row] = rowData
            tableData = arr
        }
    }

    function item(row, column) {
        if (row >= 0 && row < tableData.length && column >= 0 && column < columns.length) {
            var val = tableData[row][columns[column].role]
            return { text: (val === null || val === undefined) ? "" : val, row: row, column: column }
        }
        return null
    }

    // Selection API 选择 API
    function selectedItems() {
        var result = []
        for (var i = 0; i < selectedRows.length; i++) {
            var row = selectedRows[i]
            for (var c = 0; c < columns.length; c++) {
                result.push(item(row, c))
            }
        }
        return result
    }

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

    // Sorting API 排序 API
    function sortItems(column, order) {
        if (column < 0 || column >= columns.length) return
        if (!_isPureJsArray()) { console.warn("TableWidget: Cannot sortItems via JS when a QAbstractListModel is bound."); return }
        var role = columns[column].role
        var arr = tableData.slice()
        var currentValid = currentRow >= 0 && currentRow < arr.length
        var currentRef = currentValid ? arr[currentRow] : null
        var selectedRefs = _rowRefs(selectedRows, arr)
        var widgetEntries = _captureCellWidgetEntries(arr)
        arr.sort(function(a, b) {
            var valueA = a[role]
            var valueB = b[role]
            var textA = String((valueA === null || valueA === undefined) ? "" : valueA)
            var textB = String((valueB === null || valueB === undefined) ? "" : valueB)
            var cmp = textA.localeCompare(textB)
            return order === 1 ? -cmp : cmp
        })
        tableData = arr
        currentRow = currentValid ? arr.indexOf(currentRef) : -1
        selectedRows = _rowIndices(selectedRefs, arr)
        _restoreCellWidgets(widgetEntries, arr)
    }

    // Scroll API 滚动 API
    function scrollToTop() { listView.positionViewAtBeginning() }
    function scrollToBottom() { listView.positionViewAtEnd() }
    function scrollToRow(row) { if (row >= 0 && row < rowCount) listView.positionViewAtIndex(row, ListView.Center) }

    // setData convenience API setData 便捷 API
    // Set data from 2D array with optional headers 从二维数组设置数据
    function setData(data, headers) {
        if (headers) setHorizontalHeaderLabels(headers)
        if (!data || !data.length) { tableData = []; return }

        var cols = columns.length > 0 ? columns : []
        if (cols.length === 0 && data[0]) {
            var colCount = Array.isArray(data[0]) ? data[0].length : Object.keys(data[0]).length
            for (var c = 0; c < colCount; c++) {
                cols.push({ text: "Col " + (c+1), width: 1.0 / colCount, role: "col" + c })
            }
            columns = cols
        }

        var result = []
        for (var r = 0; r < data.length; r++) {
            var rowObj = {}
            if (Array.isArray(data[r])) {
                for (var c2 = 0; c2 < data[r].length && c2 < cols.length; c2++) {
                    rowObj[cols[c2].role] = data[r][c2]
                }
            } else {
                rowObj = data[r]
            }
            result.push(rowObj)
        }
        tableData = result
    }

    // Cell widget support 单元格控件支持
    // Set widget in cell 在单元格中放置控件
    function setCellWidget(row, column, widget) {
        if (!widget) return
        var key = row + "_" + column
        var newWidgets = Object.assign({}, cellWidgets)
        newWidgets[key] = widget
        cellWidgets = newWidgets
        // console.log("[TableWidget] setCellWidget:", row, column, widget)
    }

    // Get widget from cell 获取单元格控件
    function cellWidget(row, column) {
        var key = row + "_" + column
        return cellWidgets[key] || null
    }

    // Check if cell has widget 检查单元格是否有控件
    function hasCellWidget(row, column) {
        var key = row + "_" + column
        return cellWidgets.hasOwnProperty(key)
    }

    function _showDefaultContextMenu(rowIndex, x, y) {
        defaultTableContextMenu.showMenu(rowIndex, x, y)
    }

    // ==================== Size 尺寸 ====================
    // Base configuration 基类配置
    itemCount: rowCount
    listModel: tableData
    showHeader: columns.length > 0

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

    contentDelegate: TableInternal.TableRowDelegate {
        table: root
        radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small
    }

    // ==================== Content 内容 ====================
    headerContent: Component {
        TableInternal.TableHeader {
            table: root
        }
    }

    // 仅当 tableData 是真正的 QAbstractListModel/QObject (有 modelReset 等 signal) 才订阅;
    // QVariantList 没这些 signal, 直接绑 target 会被识别成 QObject 报警告
    // "Unable to assign QVariantList to QObject*"
    Connections {
        function onModelReset() { root.rowCount = root._calcRowCount(); root._recomputeColumnWidths() }
        function onRowsInserted() { root.rowCount = root._calcRowCount(); root._recomputeColumnWidths() }
        function onRowsRemoved() { root.rowCount = root._calcRowCount(); root._recomputeColumnWidths() }
        function onLayoutChanged() { root.rowCount = root._calcRowCount(); root._recomputeColumnWidths() }
        function onCountChanged() { root.rowCount = root._calcRowCount(); root._recomputeColumnWidths() }

        target: (root.tableData && typeof root.tableData.length !== 'number'
                 && typeof root.tableData === 'object'
                 && (typeof root.tableData.rowCount === 'function'
                     || root.tableData.modelReset !== undefined))
                ? root.tableData : null
        ignoreUnknownSignals: true
        // model 数据变化时既要刷新 rowCount 也要重算 autoWidth 列宽
        // (列宽算法采样真实数据, 空 model 时算的宽度毫无意义)
    }

    // Built-in context menu 默认内置上下文菜单
    ContextMenu {
        id: defaultTableContextMenu

        property int activeRowIndex: -1

        function showMenu(rowIndex, x, y) {
            activeRowIndex = rowIndex
            popup(x, y, root)
        }

        autoBindRightClick: false

        Action {
            text: "复制所选行 (Copy Row)"
            icon: "Copy"
            onTriggered: {
                if (defaultTableContextMenu.activeRowIndex >= 0) {
                    var rowData = root.getRow(defaultTableContextMenu.activeRowIndex)
                    if (rowData) {
                        var textParts = []
                        for (var i = 0; i < root.columns.length; i++) {
                            textParts.push(rowData[root.columns[i].role] || "")
                        }
                        ClipboardHelper.copy(textParts.join("\t"))
                    }
                }
            }
        }

        MenuSeparator {}

        Action {
            text: "在上方插入空行 (Insert Row Above)"
            icon: "Add"
            onTriggered: {
                if (defaultTableContextMenu.activeRowIndex >= 0) {
                    if (!root._isPureJsArray()) { console.warn("TableWidget: Cannot insert row via built-in menu when a QAbstractListModel is bound."); return }
                    var arr = root.tableData.slice()
                    arr.splice(defaultTableContextMenu.activeRowIndex, 0, {})
                    root.tableData = arr
                }
            }
        }

        Action {
            text: "在下方插入空行 (Insert Row Below)"
            icon: "Add"
            onTriggered: {
                if (defaultTableContextMenu.activeRowIndex >= 0) {
                    if (!root._isPureJsArray()) { console.warn("TableWidget: Cannot insert row via built-in menu when a QAbstractListModel is bound."); return }
                    var arr = root.tableData.slice()
                    arr.splice(defaultTableContextMenu.activeRowIndex + 1, 0, {})
                    root.tableData = arr
                }
            }
        }

        MenuSeparator {}

        Action {
            text: "删除受指行 (Delete Row)"
            icon: "Delete"
            onTriggered: {
                if (defaultTableContextMenu.activeRowIndex >= 0) {
                    root.removeRow(defaultTableContextMenu.activeRowIndex)
                }
            }
        }
    }

    // Pagination Component 分页器组件（仅在启用时显示）
    Loader {
        id: paginationLoader
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: Enums.spacing.m
        height: item ? item.height : 0
        active: root.showPagination
        visible: active

        sourceComponent: Component {
            Paginator {
                anchors.centerIn: parent
                currentPage: root.currentPage
                totalPages: root.totalPages
                visiblePages: root.visiblePages
                accentColor: root.checkedColor
                onPageChanged: (page) => {
                    root.currentPage = page
                    root.pageChanged(page)
                }
            }
        }
    }
}
