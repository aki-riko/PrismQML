// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../icons"
import "../inputs/Search/_internal" as SearchInternal

// CommandPalette - Ctrl+K style command surface 命令面板
//
// 模态页内浮层(不是下拉弹层): 遮罩 + 顶部居中面板 + 搜索框 + 结果列表.
// 过滤、模糊匹配、分组标题、命中高亮、↑↓ 移动、Enter 命中、空态全部复用
// SearchResultList; 本组件只负责开合、遮罩、焦点、键盘路由、命令派发与外观.
//
// 用法 / Usage:
//   Fluent.CommandPalette {
//       id: palette
//       shortcut: "Ctrl+K"
//       placeholderText: "Type a command..."
//       items: [
//           { key: "open", title: "Open File", subtitle: "Ctrl+O",
//             icon: Enums.iconPath + "FolderOpen.svg", section: "File" }
//       ]
//       onCommandTriggered: (key, item) => runCommand(key)
//   }
OverlayDialogCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var items: []
    property string placeholderText: ""
    property string emptyText: ""   // Empty-state text; caller supplies localized copy 空态文案由调用方本地化
    property string hintText: ""    // Footer hint; empty hides the footer 底部提示; 为空则隐藏
    // Optional global shortcut, e.g. "Ctrl+K"; empty disables it 可选全局快捷键, 为空则关闭
    property string shortcut: ""
    property var matchKeys: ["title", "subtitle", "keywords", "key"]
    property bool fuzzyMatch: true
    property int maxResults: 50
    property bool sectionHeaders: true
    property bool highlightMatches: true
    property color highlightColor: Enums.accentColor
    // Rows visible before the result list starts scrolling 结果列表滚动前可见行数
    property int visibleRows: 8

    // ==================== Internal Props 内部属性 ====================
    readonly property var _safeItems:
        items === null || items === undefined ? []
        : (typeof items.length === "number" ? items : [])
    readonly property int _listHeight: Math.max(
        Enums.searchMetrics.resultEmptyHeight,
        Math.min(resultList.implicitHeight,
                 Enums.searchMetrics.resultItemHeight * Math.max(1, visibleRows)))

    // ==================== Readonly State 只读状态 ====================
    readonly property bool isOpen: control._isOpen
    readonly property string query: searchField.text
    readonly property int resultCount: resultList.hitCount

    // ==================== Signals 信号 ====================
    signal commandTriggered(string key, var item)

    // ==================== Public Methods 公开方法 ====================
    function toggle() {
        if (_isOpen) close()
        else open()
    }
    function setQuery(text) { searchField.setText(text) }
    function resetQuery() { searchField.setText("") }

    // ==================== Internal Methods 内部方法 ====================
    // Every open starts from an empty query and takes the keyboard
    // 每次打开都从空查询开始, 并收下键盘焦点
    function _prepareOpen() {
        searchField.setText("")
        Qt.callLater(control._focusSearch)
    }
    function _focusSearch() {
        if (!control._isOpen) return
        searchField.forceActiveFocus()
        // LineEdit forwards focus to its inner TextInput; do it explicitly too so the
        // palette owns the keyboard on the very first open.
        // LineEdit 会把焦点转给内部 TextInput; 这里显式再转一次, 保证首次打开就拿到键盘。
        if (searchField.textInput && !searchField.textInput.activeFocus) {
            searchField.textInput.forceActiveFocus()
        }
    }
    function _keyFor(entry) {
        if (!entry) return ""
        if (entry.key !== undefined) return String(entry.key)
        return entry.title !== undefined ? String(entry.title) : ""
    }
    // Close first so the host sees a settled state when it reacts
    // 先关闭再派发, 宿主响应时状态已收敛
    function _run(entry) {
        var key = control._keyFor(entry)
        control.close()
        control.commandTriggered(key, entry)
    }

    // Modal in-window surface: the scrim dismisses, everything else stays on the panel
    // 模态页内浮层: 遮罩负责关闭, 其余交互都留在面板上
    dismissOnScrimClick: true
    maskColor: Enums.stateColor.maskHeavy

    // ==================== Content 内容 ====================
    Shortcut {
        sequence: control.shortcut
        enabled: control.shortcut !== "" && !control._isOpen
        onActivated: control.open()
    }

    // Key routing lives at window level on purpose: the search field owns the focus,
    // and its TextInput swallows arrow keys before they can bubble to the panel.
    // 键路由刻意放在窗口级: 焦点在搜索框上, 其 TextInput 会先吞掉方向键, 事件冒泡
    // 不到面板。开启期间由 Shortcut 直接接走。
    Shortcut {
        sequence: "Up"
        enabled: control._isOpen
        onActivated: resultList.moveUp()
    }
    Shortcut {
        sequence: "Down"
        enabled: control._isOpen
        onActivated: resultList.moveDown()
    }
    Shortcut {
        sequence: "Return"
        enabled: control._isOpen
        onActivated: resultList.selectCurrent()
    }
    Shortcut {
        sequence: "Enter"
        enabled: control._isOpen
        onActivated: resultList.selectCurrent()
    }
    Shortcut {
        sequence: "Escape"
        enabled: control._isOpen
        onActivated: control.close()
    }

    ShadowedRectangle {
        id: panel

        anchors.horizontalCenter: parent.horizontalCenter
        // Upper-third placement, Fluent's spot for a command surface
        // 上三分之一处, Fluent 命令面板的位置
        y: Math.max(
            Enums.spacing.xxl,
            (parent.height - height) * Enums.controlSize.commandPaletteTopRatio)
        width: Math.min(
            Enums.controlSize.commandPaletteWidth,
            Math.max(Enums.controlSize.menuMinWidth, parent.width - Enums.spacing.xxl * 2))
        height: Math.min(
            body.implicitHeight + Enums.border.thin * 2,
            Math.max(Enums.controlSize.inputHeight * 3, parent.height - Enums.spacing.xxl * 2))
        radius: Enums.radius.large
        color: Enums.dialogColor
        border.width: Enums.border.thin
        border.color: Enums.borderColor
        shadowLevel: Enums.shadow.level28

        // Swallow clicks and wheel so they never reach the scrim or the page below
        // 吞掉点击与滚轮, 不让它们穿到遮罩或下层页面
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            onWheel: (wheel) => wheel.accepted = true
        }

        Column {
            id: body
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: Enums.border.thin

            // Search row 搜索行
            Item {
                id: header
                width: parent.width
                height: Enums.controlSize.inputHeightLarge

                Icon {
                    id: searchIcon
                    anchors.left: parent.left
                    anchors.leftMargin: Enums.spacing.m
                    anchors.verticalCenter: parent.verticalCenter
                    icon: Enums.icon.search
                    iconSize: Enums.iconSize.m
                    color: Enums.textColor.secondary
                }

                LineEdit {
                    id: searchField
                    anchors.left: searchIcon.right
                    anchors.right: parent.right
                    anchors.leftMargin: Enums.spacing.s
                    anchors.verticalCenter: parent.verticalCenter
                    inputType: Enums.input.type_search
                    placeholderText: control.placeholderText
                    clearButtonEnabled: true
                    // Enter/↑↓/Esc are routed by the window-level shortcuts above
                    // 回车/↑↓/Esc 由上面的窗口级快捷键路由
                }
            }

            Rectangle {
                width: parent.width
                height: Enums.border.thin
                color: Enums.dividerColor
            }

            // Ranked, highlighted, grouped results 排名/高亮/分组结果
            Item {
                id: results
                width: parent.width
                height: control._listHeight

                SearchInternal.SearchResultList {
                    id: resultList
                    anchors.fill: parent
                    query: searchField.text
                    entries: control._safeItems
                    matchKeys: control.matchKeys
                    fuzzyMatch: control.fuzzyMatch
                    maxSuggestions: control.maxResults
                    sectionHeaders: control.sectionHeaders
                    highlightMatches: control.highlightMatches
                    highlightColor: control.highlightColor
                    emptyText: {
                        Translator._v
                        return control.emptyText || Translator.tr("no_results")
                    }

                    onEntrySelected: function(entry) { control._run(entry) }
                    onDismissed: control.close()
                }
            }

            Rectangle {
                width: parent.width
                height: Enums.border.thin
                color: Enums.dividerColor
                visible: footerRow.visible
            }

            // Footer hint 底部提示
            Item {
                id: footerRow
                width: parent.width
                height: visible ? Enums.controlSize.statusBarHeight + Enums.spacing.xs : 0
                visible: control.hintText !== ""

                Label {
                    anchors.left: parent.left
                    anchors.leftMargin: Enums.spacing.m
                    anchors.verticalCenter: parent.verticalCenter
                    type: Enums.label.type_caption
                    text: control.hintText
                    color: Enums.textColor.secondary
                }
            }
        }
    }
}
