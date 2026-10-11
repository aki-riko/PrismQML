// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../.."
import "../LineEdit"
import "_internal" as SearchInternal

// LocalSearchBar — 通用本地搜索控件
//
// 输入即搜索 + 下拉建议 + 键盘导航(↑↓ wrap, Enter 命中, Esc 关闭).
// 支持两种 popup 模式:
//   - AnchoredBelow: 紧贴输入框下方,等宽
//   - CenteredOverlay: 居中浮窗,固定宽 600
//
// 数据驱动: entries 是数据数组(非 children 嵌套),对齐 Raycast/VS Code
// QuickPick/Material Combobox API 风格.
//
// 受控+非受控双兼容: 不接信号也能跑(默认清空+关闭),接信号后完全控制
// 后续动作.
//
// 分组: entry.section 非空且 sectionHeaders=true 时按 section 分组显示标题行,
// 分组顺序取各 section 在排名结果中首次出现的顺序,组内保持 score 排名.
// 关闭 sectionHeaders 或所有 entry 都没有 section 时,视觉与不分组完全一致.
//
// 用法:
//   Fluent.LocalSearchBar {
//       placeholderText: '搜索设置...'
//       entries: [
//           { title: '云母效果', subtitle: '个性化', icon: 'Color',
//             section: '外观', keywords: ['mica'], data: { panelIdx: 1 } },
//           ...
//       ]
//       onEntrySelected: function(entry) {
//           console.log('selected:', entry.title)
//       }
//   }
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var entries: []
    property string placeholderText: ''
    property int popupMode: Enums.input.search_popup_anchored_below
    property var matchKeys: ['title', 'subtitle', 'keywords']
    property bool fuzzyMatch: true
    property int maxSuggestions: 5
    property bool sectionHeaders: true   // Group results by entry.section 按 entry.section 分组显示标题
    property bool highlightMatches: true
    property string emptyText: ''  // Defaults to i18n key 默认走 i18n no_results

    // Async suggestions 异步建议源
    // A function `(query, callback)`; the callback receives the suggestion array.
    // When unset the local `entries` array keeps driving the list.
    // 形如 `(query, callback)` 的函数; 回调接收建议数组。未设置时仍由本地 entries 驱动。
    property var suggestionsSource: null
    // Write the chosen suggestion back into the query 选中项是否回填到输入框
    property bool updateTextOnSelect: false
    // Entry field used when writing back a suggestion 回填时读取的条目字段
    property string textMemberPath: 'title'

    // ==================== Internal Props 内部属性 ====================
    property Item _resultList: null
    property Item _searchPopup: null
    property int _queryEditRevision: 0
    // Latest async suggestion batch 最近一次异步建议批次
    property var _suggestions: []
    // Monotonic request id used to drop stale responses 用于丢弃过期响应的递增请求号
    property int _suggestionRevision: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property string query: lineEdit.text
    readonly property bool isOpen: _searchPopup ? _searchPopup.isOpen : false
    readonly property int selectionStart: lineEdit.selectionStart
    readonly property int selectionEnd: lineEdit.selectionEnd
    readonly property string selectedText: lineEdit.selectedText
    readonly property var _safeEntries:
        entries === null || entries === undefined ? []
        : (typeof entries.length === "number" ? entries : [])
    // Active suggestion batch: async provider result or local entries
    // 生效的建议批次: 异步源结果或本地 entries
    readonly property var _activeEntries:
        suggestionsSource === null || suggestionsSource === undefined
        ? _safeEntries : _suggestions

    // ==================== Signals 信号 ====================
    signal entrySelected(var entry)
    // QuerySubmitted: free text or a chosen suggestion 提交查询: 自由文本或选中的建议
    signal querySubmitted(var args)
    // Note: queryChanged is not exposed; listen with onQueryChanged 注意: 不暴露 queryChanged — 它会跟 readonly property `query`
    // 自带的 *Changed signal 冲突. 应用层要监听用 onQueryChanged.
    signal queryEdited(string text)
    signal cleared()
    signal opened()
    signal dismissed()

    // ==================== Public Methods 公开方法 ====================
    function clear() {
        var result = lineEdit.clear()
        cleared()
        dismiss()
        return result
    }
    function selectAll() { return lineEdit.selectAll() }
    function undo() { return _dispatchQueryEditAction("undo") }
    function redo() { return _dispatchQueryEditAction("redo") }
    function copy() { return lineEdit.copy() }
    function cut() { return _dispatchQueryEditAction("cut") }
    function paste() { return _dispatchQueryEditAction("paste") }

    function open() {
        if (popupMode === Enums.input.search_popup_centered_overlay) {
            if (_ensureSearchSurface()) {
                _searchPopup.open()
                lineEdit.forceActiveFocus()
            }
        }
    }
    function dismiss() {
        if (_searchPopup) {
            _searchPopup.dismiss()
        }
    }
    function setQuery(text) {
        lineEdit.text = text || ''
        _requestSuggestions(lineEdit.text)
        // Imperative API calls popup ops directly; the core guards re-entry 命令式 API 直接调 popup 操作; 底层 PopupWindowCore 自带
        // isOpen/isClosing 守卫,重复调用幂等
        if (control.popupMode === Enums.input.search_popup_anchored_below) {
            if (lineEdit.text.length > 0) {
                if (_ensureSearchSurface()) {
                    _searchPopup.open()
                }
            } else {
                dismiss()
            }
        }
    }
    function getQuery() {
        return lineEdit.text
    }

    // ==================== Internal Methods 内部方法 ====================
    function _dispatchQueryEditAction(actionName) {
        var previousText = lineEdit.text
        var previousRevision = _queryEditRevision
        var result = lineEdit[actionName]()
        if (result && lineEdit.text !== previousText
                && _queryEditRevision === previousRevision) {
            _handleQueryEdited(lineEdit.text)
        }
        return result
    }

    function _handleQueryEdited(text) {
        _queryEditRevision += 1
        queryEdited(text)
        _requestSuggestions(text)
        _syncAnchoredPopup(text)
    }

    // Ask the async provider for suggestions 向异步源请求建议
    // Every request invalidates the previous one, so a late response is dropped.
    // 每次请求都作废上一次, 迟到的响应会被丢弃。
    function _requestSuggestions(text) {
        if (suggestionsSource === null || suggestionsSource === undefined) return
        _suggestionRevision += 1
        var revision = _suggestionRevision
        var target = control
        suggestionsSource(text, function(results) {
            if (revision !== target._suggestionRevision) return
            target._suggestions = target._suggestionList(results)
        })
    }

    // Normalise a provider response 规范化提供方返回值
    function _suggestionList(results) {
        if (results === null || results === undefined) return []
        return typeof results.length === "number" ? results : []
    }

    // Resolve the query text written back for one suggestion 解析回填到输入框的文本
    function _suggestionText(entry) {
        if (entry === null || entry === undefined) return ''
        var member = entry[textMemberPath]
        return member === undefined || member === null ? '' : String(member)
    }

    // QuerySubmitted for free text or the chosen suggestion 提交自由文本或选中建议
    function _submitQuery(chosenEntry) {
        if (chosenEntry !== null && chosenEntry !== undefined) {
            if (updateTextOnSelect) {
                lineEdit.text = _suggestionText(chosenEntry)
            } else {
                // Preserve clear-and-dismiss selection behavior 保持选中后清空并关闭
                lineEdit.text = ''
            }
            dismiss()
        }
        querySubmitted({
            chosenSuggestion: chosenEntry === undefined ? null : chosenEntry,
            queryText: lineEdit.text
        })
    }

    function _syncAnchoredPopup(text) {
        if (popupMode !== Enums.input.search_popup_anchored_below) return
        if (text.length > 0) {
            if (_ensureSearchSurface()) _searchPopup.open()
        } else {
            dismiss()
        }
    }

    // Create the search surface synchronously on first use 首次使用时同步创建搜索界面
    function _ensureSearchSurface() {
        if (!_resultList) {
            _resultList = resultListComponent.createObject(control)
            if (!_resultList) {
                console.error(
                    'LocalSearchBar: failed to create SearchResultList: '
                    + resultListComponent.errorString()
                )
                return false
            }
            // Restore the eager component's initial selection 恢复原常驻组件的初始选中项
            _resultList.reset()
        }
        if (!_searchPopup) {
            _searchPopup = searchPopupComponent.createObject(control)
            if (!_searchPopup) {
                console.error(
                    'LocalSearchBar: failed to create SearchPopup: '
                    + searchPopupComponent.errorString()
                )
                return false
            }
        }
        return true
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: lineEdit.implicitWidth
    implicitHeight: lineEdit.implicitHeight

    // ==================== Content 内容 ====================
    // Search input 搜索输入框
    LineEdit {
        id: lineEdit
        anchors.fill: parent
        inputType: Enums.input.type_search
        placeholderText: control.placeholderText
        clearButtonEnabled: true

        onTextEdited: function(text) {
            control._handleQueryEdited(text)
        }
        onCleared: {
            control.cleared()
            control.dismiss()
        }

        // Keyboard events: Enter picks, Esc closes, Up/Down move selection 键盘事件 — Enter 命中,Esc 关闭,↑↓ 切换列表项
        Keys.onUpPressed: function(event) {
            if (control.isOpen) {
                control._resultList.moveUp()
                event.accepted = true
            }
        }
        Keys.onDownPressed: function(event) {
            if (control.isOpen) {
                control._resultList.moveDown()
                event.accepted = true
            } else if (control._safeEntries.length > 0
                       && control._ensureSearchSurface()) {
                control._searchPopup.open()
                event.accepted = true
            }
        }
        Keys.onReturnPressed: function(event) {
            if (control.isOpen && control._resultList.hitCount > 0) {
                control._resultList.selectCurrent()
                event.accepted = true
            } else if (control.query.length > 0) {
                // Free-text submit keeps the historical key propagation
                // 自由文本提交保持历史按键传播行为
                control._submitQuery(null)
            }
        }
        Keys.onEnterPressed: function(event) {
            if (control.isOpen && control._resultList.hitCount > 0) {
                control._resultList.selectCurrent()
                event.accepted = true
            } else if (control.query.length > 0) {
                control._submitQuery(null)
            }
        }
        Keys.onEscapePressed: function(event) {
            if (control.isOpen) {
                control.dismiss()
                event.accepted = true
            }
        }
    }

    // Lazy result list component 延迟结果列表组件
    Component {
        id: resultListComponent

        SearchInternal.SearchResultList {
            query: control.query
            entries: control._activeEntries
            matchKeys: control.matchKeys
            fuzzyMatch: control.fuzzyMatch
            maxSuggestions: control.maxSuggestions
            sectionHeaders: control.sectionHeaders
            highlightMatches: control.highlightMatches
            emptyText: {
                Translator._v
                return control.emptyText || Translator.tr('no_results')
            }

            onEntrySelected: function(entry) {
                control.entrySelected(entry)
                control._submitQuery(entry)
            }
            onDismissed: control.dismiss()
        }
    }

    // Lazy popup component 延迟弹窗组件
    Component {
        id: searchPopupComponent

        SearchInternal.SearchPopup {
            anchorTarget: lineEdit
            popupMode: control.popupMode
            rootContent: control._resultList

            onOpened: control.opened()
            onDismissed: control.dismissed()
        }
    }
}
