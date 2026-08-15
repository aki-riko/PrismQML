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
// 用法:
//   Fluent.LocalSearchBar {
//       placeholderText: '搜索设置...'
//       entries: [
//           { title: '云母效果', subtitle: '个性化', icon: 'Color',
//             keywords: ['mica'], data: { panelIdx: 1 } },
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
    property bool sectionHeaders: true   // 暂未实现 (v2)
    property bool highlightMatches: true
    property string emptyText: ''  // 默认走 i18n no_results

    // ==================== Internal Props 内部属性 ====================
    property Item _resultList: null
    property Item _searchPopup: null
    property int _queryEditRevision: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property string query: lineEdit.text
    readonly property bool isOpen: _searchPopup ? _searchPopup.isOpen : false
    readonly property int selectionStart: lineEdit.selectionStart
    readonly property int selectionEnd: lineEdit.selectionEnd
    readonly property string selectedText: lineEdit.selectedText
    readonly property var _safeEntries:
        entries === null || entries === undefined ? []
        : (typeof entries.length === "number" ? entries : [])

    // ==================== Signals 信号 ====================
    signal entrySelected(var entry)
    // 注意: 不暴露 queryChanged — 它会跟 readonly property `query`
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
        // 命令式 API 直接调 popup 操作; 底层 PopupWindowCore 自带
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
        _syncAnchoredPopup(text)
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

        // 键盘事件 — Enter 命中,Esc 关闭,↑↓ 切换列表项
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
            }
        }
        Keys.onEnterPressed: function(event) {
            if (control.isOpen && control._resultList.hitCount > 0) {
                control._resultList.selectCurrent()
                event.accepted = true
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
            entries: control._safeEntries
            matchKeys: control.matchKeys
            fuzzyMatch: control.fuzzyMatch
            maxSuggestions: control.maxSuggestions
            highlightMatches: control.highlightMatches
            emptyText: {
                Translator._v
                return control.emptyText || Translator.tr('no_results')
            }

            onEntrySelected: function(entry) {
                control.entrySelected(entry)
                // Preserve clear-and-dismiss selection behavior 保持选中后清空并关闭
                lineEdit.text = ''
                control.dismiss()
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
