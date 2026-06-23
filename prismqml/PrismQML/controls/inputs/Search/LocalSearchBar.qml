// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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

    // ==================== popupMode 枚举 ====================
    enum PopupMode {
        AnchoredBelow = 0,
        CenteredOverlay = 1
    }

    // ==================== Public Props ====================
    property var entries: []
    property string placeholderText: ''
    property int popupMode: LocalSearchBar.PopupMode.AnchoredBelow
    property var matchKeys: ['title', 'subtitle', 'keywords']
    property bool fuzzyMatch: true
    property int maxSuggestions: 5
    property bool sectionHeaders: true   // 暂未实现 (v2)
    property bool highlightMatches: true
    property string emptyText: ''  // 默认走 i18n no_results

    // ==================== Read-only ====================
    readonly property string query: lineEdit.text
    readonly property bool isOpen: searchPopup.isOpen

    // ==================== Signals ====================
    signal entrySelected(var entry)
    // 注意: 不暴露 queryChanged — 它会跟 readonly property `query`
    // 自带的 *Changed signal 冲突. 应用层要监听用 onQueryChanged.
    signal queryEdited(string text)
    signal cleared()
    signal opened()
    signal dismissed()

    // ==================== Sizing ====================
    implicitWidth: lineEdit.implicitWidth
    implicitHeight: lineEdit.implicitHeight

    // ==================== Public methods ====================
    function open() {
        if (popupMode === LocalSearchBar.PopupMode.CenteredOverlay) {
            searchPopup.open()
            lineEdit.forceActiveFocus()
        }
    }
    function dismiss() {
        searchPopup.dismiss()
    }
    function setQuery(text) {
        lineEdit.text = text || ''
        // 命令式 API 直接调 popup 操作; 底层 PopupWindowCore 自带
        // isOpen/isClosing 守卫,重复调用幂等
        if (control.popupMode === LocalSearchBar.PopupMode.AnchoredBelow) {
            if (lineEdit.text.length > 0) {
                searchPopup.open()
            } else {
                searchPopup.dismiss()
            }
        }
    }
    function getQuery() {
        return lineEdit.text
    }

    // ==================== LineEdit (输入框) ====================
    LineEdit {
        id: lineEdit
        anchors.fill: parent
        inputType: Enums.input.type_search
        placeholderText: control.placeholderText
        clearButtonEnabled: true

        onTextEdited: function(text) {
            control.queryEdited(text)
            // AnchoredBelow: 输入立即唤起 popup, 清空时关闭
            // 重复调用幂等(底层 PopupWindowCore 自带守卫)
            if (control.popupMode === LocalSearchBar.PopupMode.AnchoredBelow) {
                if (text.length > 0) searchPopup.open()
                else searchPopup.dismiss()
            }
        }
        onCleared: {
            control.cleared()
            searchPopup.dismiss()
        }

        // 键盘事件 — Enter 命中,Esc 关闭,↑↓ 切换列表项
        Keys.onUpPressed: function(event) {
            if (searchPopup.isOpen) { resultList.moveUp(); event.accepted = true }
        }
        Keys.onDownPressed: function(event) {
            if (searchPopup.isOpen) { resultList.moveDown(); event.accepted = true }
            else if (control.entries.length > 0) {
                searchPopup.open()
                event.accepted = true
            }
        }
        Keys.onReturnPressed: function(event) {
            if (searchPopup.isOpen && resultList.hitCount > 0) {
                resultList.selectCurrent()
                event.accepted = true
            }
        }
        Keys.onEnterPressed: function(event) {
            if (searchPopup.isOpen && resultList.hitCount > 0) {
                resultList.selectCurrent()
                event.accepted = true
            }
        }
        Keys.onEscapePressed: function(event) {
            if (searchPopup.isOpen) {
                searchPopup.dismiss()
                event.accepted = true
            }
        }
    }

    // ==================== Popup + ResultList (打包) ====================
    SearchInternal.SearchResultList {
        id: resultList
        query: control.query
        entries: control.entries
        matchKeys: control.matchKeys
        fuzzyMatch: control.fuzzyMatch
        maxSuggestions: control.maxSuggestions
        highlightMatches: control.highlightMatches
        emptyText: control.emptyText || Translator.tr('no_results')

        onEntrySelected: function(entry) {
            control.entrySelected(entry)
            // 默认行为: 选中后清空 + 关闭
            lineEdit.text = ''
            searchPopup.dismiss()
        }
        onDismissed: searchPopup.dismiss()
    }

    SearchInternal.SearchPopup {
        id: searchPopup
        anchorTarget: lineEdit
        popupMode: control.popupMode
        rootContent: resultList

        onOpened: control.opened()
        onDismissed: control.dismissed()
    }
}
