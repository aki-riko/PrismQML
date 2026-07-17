// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick.Layouts
import "../../../.."
import "../../../data/Label"
import "FuzzyMatcher.js" as FM
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// SearchResultList — 搜索结果列表 + 键盘导航 + 空态
//
// 输入: query (string) + entries (array of {title, subtitle, icon, section, keywords, data})
// 输出: signal entrySelected(var entry) / signal dismissed()
//
// 内部:
//   1. query 变化 → FM.filterAndRank → _hits 数组
//   2. ListView 渲染 _hits, delegate 用 SearchResultItem
//   3. 键盘:
//      ↑/↓: currentIndex--/++, wrap 到 last/0
//      Enter: emit entrySelected(_hits[currentIndex].entry)
//      Esc:   emit dismissed()
//   4. 空 _hits: 显示 emptyText
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
    property string emptyText: ''  // 空时显示文案,父级注入(走 i18n)
    property color highlightColor: Enums.accentColor
    property int itemHeight: Enums.searchMetrics.resultItemHeight

    // ==================== Readonly State 只读状态 ====================
    // _hits: [{entry, score, fieldRanges}, ...]
    readonly property var _hits: FM.filterAndRank(
        query, entries, matchKeys, undefined, fuzzyMatch, maxSuggestions
    )
    readonly property int hitCount: _hits ? _hits.length : 0
    readonly property bool isEmpty: hitCount === 0

    // ==================== Signals 信号 ====================
    signal entrySelected(var entry)
    signal dismissed()

    // ==================== Public Methods 公开方法 ====================
    function selectCurrent() {
        if (listView.currentIndex >= 0 && listView.currentIndex < hitCount) {
            entrySelected(_hits[listView.currentIndex].entry)
        }
    }

    function moveUp() {
        if (hitCount === 0) return
        listView.currentIndex = (listView.currentIndex - 1 + hitCount) % hitCount
        listView.positionViewAtIndex(listView.currentIndex, ListView.Contain)
    }

    function moveDown() {
        if (hitCount === 0) return
        listView.currentIndex = (listView.currentIndex + 1) % hitCount
        listView.positionViewAtIndex(listView.currentIndex, ListView.Contain)
    }

    function reset() {
        listView.currentIndex = hitCount > 0 ? 0 : -1
    }

    // ==================== Internal Methods 内部方法 ====================
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

    // 当 _hits 变化时,重置 currentIndex 到 0 (跟 query 输入一致)
    on_HitsChanged: reset()

    // ==================== Size 尺寸 ====================
    // 高度严格按实际命中数计算,不预留空间:
    //   isEmpty           → 60 (空态文字一行 + padding)
    //   非 isEmpty 1 项   → 1*itemHeight + padding
    //   非 isEmpty N 项   → min(maxSuggestions, N) 项 (含 spacing) + padding
    // 超过 maxSuggestions 才滚动
    implicitWidth: Enums.searchMetrics.resultListWidth
    implicitHeight: {
        if (isEmpty) return Enums.searchMetrics.resultEmptyHeight
        var displayCount = Math.min(maxSuggestions, hitCount)
        // Reuse the ListView spacing and margins tokens 复用列表项间距与边距 token
        return displayCount * itemHeight
            + (displayCount - 1) * Enums.spacing.xxs
            + 2 * Enums.spacing.xs
    }

    // ==================== Content 内容 ====================
    Item {
        anchors.fill: parent

        // 空态
        Label {
            anchors.centerIn: parent
            visible: control.isEmpty
            text: control.emptyText
            type: Enums.label.type_body
            color: Enums.textColor.secondary
        }

        // 列表
        ListView {
            id: listView
            anchors.fill: parent
            anchors.margins: Enums.spacing.xs
            visible: !control.isEmpty
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            interactive: true
            keyNavigationEnabled: false  // 自己处理避免冲突
            currentIndex: 0
            highlightMoveDuration: Enums.duration.fast

            model: control._hits
            spacing: Enums.spacing.xxs

            // 滚动条由父 popup 容器决定 (TipPopup / PopupWindowCore 内部已带)

            delegate: Loader {
                property var hitData: modelData
                property int hitIndex: index

                width: ListView.view ? ListView.view.width : 0
                height: control.itemHeight
                sourceComponent: itemComponent
            }
        }

        // 把 SearchResultItem 用 Loader 包,避免 required property
        // 在 ListView 直接 delegate 时的 binding 时序坑
        Component {
            id: itemComponent

            SearchResultItem {
                itemIndex: parent.hitIndex
                entryData: parent.hitData ? parent.hitData.entry : null
                highlightedTitle: control._renderHighlight(
                    entryData ? entryData.title : '',
                    parent.hitData && parent.hitData.fieldRanges ? parent.hitData.fieldRanges.title : null
                )
                highlightedSubtitle: control._renderHighlight(
                    entryData ? entryData.subtitle : '',
                    parent.hitData && parent.hitData.fieldRanges ? parent.hitData.fieldRanges.subtitle : null
                )
                selected: listView.currentIndex === parent.hitIndex

                onClicked: {
                    listView.currentIndex = parent.hitIndex
                    control.selectCurrent()
                }
            }
        }
    }
}
