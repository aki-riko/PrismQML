// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick.Layouts
import "../../../.."
import "../../../data/Label"
import "FuzzyMatcher.js" as FM
import QtQuick  // After library import: unprefixed native types stay unshadowed 置于库import后:去前缀后保原生类型不被库覆盖

// SearchResultList — 搜索结果列表 + 分组标题 + 键盘导航 + 空态
// SearchResultList — search result list + section headers + keyboard nav + empty state
//
// 输入: query (string) + entries (array of {title, subtitle, icon, section, keywords, data})
// 输出: signal entrySelected(var entry) / signal dismissed()
//
// sectionHeaders 分组:
//   entries 里任一 entry 带非空 section 且 sectionHeaders=true 时按 section 分组;
//   分组顺序取各 section 在排名结果中首次出现的顺序, 组内保持原有 score 排名.
//   无 section 的 entry 归入一个无标题分组, 同样按其首次出现顺序占位.
//   分组键为空的组不渲染标题行.
//
// 内部:
//   1. query 变化 → FM.filterAndRank → _hits 数组
//   2. _hits + sectionHeaders → _rows (标题行 + 结果行扁平模型)
//   3. ListView 渲染 _rows, delegate 用 SearchSectionHeader / SearchResultItem
//   4. 键盘(光标只在结果行之间移动, 标题行跳过):
//      ↑/↓: 结果序 --/++, wrap 到 last/0
//      Enter: emit entrySelected(_hits[_itemCursor].entry)
//      Esc:   emit dismissed()
//   5. 空 _hits: 显示 emptyText
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string query: ''
    property var entries: []
    property var matchKeys: ['title', 'subtitle', 'keywords']
    property bool fuzzyMatch: true
    property int maxSuggestions: 5
    property bool sectionHeaders: true
    property bool highlightMatches: true
    property string emptyText: ''  // Empty-state text, injected by parent (i18n) 空时显示文案,父级注入(走 i18n)
    property color highlightColor: Enums.accentColor
    property int itemHeight: Enums.searchMetrics.resultItemHeight

    // ==================== Internal Props 内部属性 ====================
    // Cursor lives in result space (headers excluded) 光标位于结果序(不含标题行)
    property int _itemCursor: 0

    // ==================== Readonly State 只读状态 ====================
    // _hits: [{entry, score, fieldRanges}, ...]
    readonly property var _hits: FM.filterAndRank(
        query, entries, matchKeys, undefined, fuzzyMatch, maxSuggestions
    )
    readonly property int hitCount: _hits ? _hits.length : 0
    readonly property bool isEmpty: hitCount === 0
    // _rows: [{kind: 'header'|'item', key, title?, hit?, itemOrdinal?}, ...]
    readonly property var _rows: _buildRows()

    // ==================== Signals 信号 ====================
    signal entrySelected(var entry)
    signal dismissed()

    // ==================== Public Methods 公开方法 ====================
    function selectCurrent() {
        var hit = _hitForOrdinal(control._itemCursor)
        if (hit) {
            entrySelected(hit.entry)
        }
    }

    function moveUp() {
        if (hitCount === 0) return
        _setCursor((control._itemCursor - 1 + hitCount) % hitCount)
    }

    function moveDown() {
        if (hitCount === 0) return
        _setCursor((control._itemCursor + 1) % hitCount)
    }

    function reset() {
        _setCursor(hitCount > 0 ? 0 : -1)
    }

    // ==================== Internal Methods 内部方法 ====================
    // Move the result cursor and mirror it onto the row-space ListView index 移动结果光标并同步到行序 ListView 索引
    function _setCursor(ordinal) {
        control._itemCursor = ordinal
        _syncRowIndex()
    }

    // Re-assert the ListView row index for the current cursor 重新对齐当前光标对应的行索引
    function _syncRowIndex() {
        if (!listView) return
        var rowIndex = control._rowForOrdinal(control._itemCursor)
        if (listView.currentIndex === rowIndex) return
        listView.currentIndex = rowIndex
        if (rowIndex >= 0) {
            listView.positionViewAtIndex(rowIndex, ListView.Contain)
        }
    }

    // Map a result ordinal to its row index (-1 when absent) 结果序号映射到行索引(不存在返回 -1)
    function _rowForOrdinal(ordinal) {
        var rows = control._rows
        if (!rows) return -1
        for (var i = 0; i < rows.length; i++) {
            if (rows[i].kind === 'item' && rows[i].itemOrdinal === ordinal) {
                return i
            }
        }
        return -1
    }

    // Map a result ordinal to the hit it displays (display order != rank order when grouped)
    // 结果序号映射到它显示的命中 (分组后显示序与排名序不同)
    function _hitForOrdinal(ordinal) {
        var rowIndex = _rowForOrdinal(ordinal)
        if (rowIndex < 0) return null
        return control._rows[rowIndex].hit
    }

    function _isHeaderRow(row) {
        return !!row && row.kind === 'header'
    }

    function _rowHeight(row) {
        return _isHeaderRow(row)
            ? Enums.searchMetrics.resultSectionHeaderHeight : control.itemHeight
    }

    // Normalized section key of a hit ('' when absent) 命中的归一化分组键(缺失为空串)
    function _sectionKey(hit) {
        if (!hit || !hit.entry) return ''
        var value = hit.entry.section
        if (value === undefined || value === null) return ''
        return String(value)
    }

    function _flatRows(hits) {
        var rows = []
        for (var i = 0; i < hits.length; i++) {
            rows.push({ kind: 'item', key: '', hit: hits[i], itemOrdinal: i })
        }
        return rows
    }

    // Build the flat row model; grouping only when sections are present 构建扁平行模型; 仅在有分组时分组
    function _buildRows() {
        var hits = control._hits
        if (!hits || hits.length === 0) return []
        if (!control.sectionHeaders) return _flatRows(hits)

        var hasSection = false
        for (var probe = 0; probe < hits.length; probe++) {
            if (_sectionKey(hits[probe]).length > 0) {
                hasSection = true
                break
            }
        }
        if (!hasSection) return _flatRows(hits)

        var order = []
        var groups = {}
        for (var i = 0; i < hits.length; i++) {
            var key = _sectionKey(hits[i])
            if (!Object.prototype.hasOwnProperty.call(groups, key)) {
                groups[key] = []
                order.push(key)
            }
            groups[key].push(hits[i])
        }

        var rows = []
        var ordinal = 0
        for (var g = 0; g < order.length; g++) {
            var groupKey = order[g]
            var bucket = groups[groupKey]
            if (groupKey.length > 0) {
                rows.push({ kind: 'header', key: groupKey, title: groupKey })
            }
            for (var b = 0; b < bucket.length; b++) {
                rows.push({
                    kind: 'item', key: groupKey, hit: bucket[b], itemOrdinal: ordinal
                })
                ordinal += 1
            }
        }
        return rows
    }

    // Render highlighted HTML text 渲染高亮 HTML 文本
    function _renderHighlight(text, ranges) {
        if (!text) return ''
        if (!ranges || !control.highlightMatches || ranges.length === 0) {
            return _escapeHtml(text)
        }

        var out = ''
        var cursor = 0
        var color = control.highlightColor.toString()
        for (var i = 0; i < ranges.length; i++) {
            var s = ranges[i][0]
            var e = ranges[i][1]
            if (s > cursor) {
                out += _escapeHtml(text.substring(cursor, s))
            }
            out += '<b style="color:' + color + '">' + _escapeHtml(text.substring(s, e)) + '</b>'
            cursor = e
        }
        if (cursor < text.length) {
            out += _escapeHtml(text.substring(cursor))
        }
        return out
    }

    function _escapeHtml(s) {
        if (!s) return ''
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;')
    }

    // Reset follows the *semantic* inputs: a new query or a replaced result set puts
    // the cursor back on the top hit. An incidental re-ranking with the same inputs
    // (a host reading implicitHeight, for example) must not steal the cursor, or
    // arrow navigation is silently undone before Enter.
    // 重置跟随语义输入: 新查询或结果集被替换时把光标收回首个命中。相同输入下的偶然
    // 重新排名(例如宿主读取隐式高度)不得夺走光标, 否则方向键移动会在回车前被静默撤销。
    onQueryChanged: reset()
    onEntriesChanged: reset()
    on_HitsChanged: if (control._itemCursor >= hitCount) reset()
    // Row layout changes when grouping toggles 分组开关变化会改变行布局
    onSectionHeadersChanged: reset()
    // The ListView may rewrite currentIndex while the row model resettles 行模型重建期间 ListView 可能改写 currentIndex
    on_RowsChanged: _syncRowIndex()

    // ==================== Size 尺寸 ====================
    // 高度严格按实际行数计算,不预留空间:
    //   isEmpty      → 60 (空态文字一行 + padding)
    //   非 isEmpty   → Σ行高 (结果行 itemHeight / 标题行 resultSectionHeaderHeight)
    //                  + 行间距 + 上下 padding
    // 超过 maxSuggestions 才滚动
    implicitWidth: Enums.searchMetrics.resultListWidth
    implicitHeight: {
        if (isEmpty) return Enums.searchMetrics.resultEmptyHeight
        var rows = control._rows
        if (!rows || rows.length === 0) return Enums.searchMetrics.resultEmptyHeight
        var total = 0
        for (var i = 0; i < rows.length; i++) {
            total += control._rowHeight(rows[i])
        }
        // Reuse the ListView spacing and margins tokens 复用列表项间距与边距 token
        return total
            + (rows.length - 1) * Enums.spacing.xxs
            + 2 * Enums.spacing.xs
    }

    // ==================== Content 内容 ====================
    Item {
        anchors.fill: parent

        // Empty state 空态
        Label {
            anchors.centerIn: parent
            visible: control.isEmpty
            text: control.emptyText
            type: Enums.label.type_body
            color: Enums.textColor.secondary
        }

        // List 列表
        ListView {
            id: listView
            anchors.fill: parent
            anchors.margins: Enums.spacing.xs
            visible: !control.isEmpty
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            interactive: true
            keyNavigationEnabled: false  // Handle locally to avoid conflicts 自己处理避免冲突
            currentIndex: 0
            highlightMoveDuration: Enums.duration.fast

            model: control._rows
            spacing: Enums.spacing.xxs

            // Delegate rebuilds can drop the cursor back to row 0 委托重建可能把光标拉回第 0 行
            onCountChanged: control._syncRowIndex()

            // Scrollbar owned by the parent popup container 滚动条由父 popup 容器决定 (TipPopup / PopupWindowCore 内部已带)

            delegate: Loader {
                property var rowData: modelData
                property int rowIndex: index

                width: ListView.view ? ListView.view.width : 0
                height: control._rowHeight(rowData)
                sourceComponent: control._isHeaderRow(rowData)
                    ? headerComponent : itemComponent
            }
        }

        // Section header row 分组标题行
        Component {
            id: headerComponent

            Item {
                // Loader-owned row payload 由 Loader 持有的行数据
                readonly property var rowData: parent ? parent.rowData : null

                Label {
                    anchors.left: parent.left
                    anchors.leftMargin: Enums.spacing.l
                    anchors.right: parent.right
                    anchors.rightMargin: Enums.spacing.l
                    anchors.verticalCenter: parent.verticalCenter
                    text: parent.rowData ? parent.rowData.title : ''
                    type: Enums.label.type_caption
                    color: Enums.textColor.secondary
                    elide: Text.ElideRight
                    wrapMode: Text.NoWrap
                }
            }
        }

        // Wrap SearchResultItem in a Loader to dodge delegate binding-order issues 把 SearchResultItem 用 Loader 包,避免 required property
        // 在 ListView 直接 delegate 时的 binding 时序坑
        Component {
            id: itemComponent

            SearchResultItem {
                itemIndex: parent.rowData && parent.rowData.hit
                    ? parent.rowData.itemOrdinal : 0
                entryData: parent.rowData && parent.rowData.hit
                    ? parent.rowData.hit.entry : null
                highlightedTitle: control._renderHighlight(
                    entryData ? entryData.title : '',
                    parent.rowData && parent.rowData.hit && parent.rowData.hit.fieldRanges
                        ? parent.rowData.hit.fieldRanges.title : null
                )
                highlightedSubtitle: control._renderHighlight(
                    entryData ? entryData.subtitle : '',
                    parent.rowData && parent.rowData.hit && parent.rowData.hit.fieldRanges
                        ? parent.rowData.hit.fieldRanges.subtitle : null
                )
                selected: control._itemCursor === itemIndex

                onClicked: {
                    control._setCursor(itemIndex)
                    control.selectCurrent()
                }
            }
        }
    }
}
