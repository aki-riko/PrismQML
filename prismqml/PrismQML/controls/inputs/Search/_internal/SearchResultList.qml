// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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

    // ==================== Public Props ====================
    property string query: ''
    property var entries: []
    property var matchKeys: ['title', 'subtitle', 'keywords']
    property bool fuzzyMatch: true
    property int maxSuggestions: 5
    property bool sectionHeaders: true
    property bool highlightMatches: true
    property string emptyText: ''  // 空时显示文案,父级注入(走 i18n)
    property color highlightColor: Enums.accentColor
    property int itemHeight: 48

    // ==================== Read-only computed ====================
    // _hits: [{entry, score, fieldRanges}, ...]
    readonly property var _hits: FM.filterAndRank(
        query, entries, matchKeys, undefined, fuzzyMatch, maxSuggestions
    )
    readonly property int hitCount: _hits ? _hits.length : 0
    readonly property bool isEmpty: hitCount === 0

    // ==================== Signals ====================
    signal entrySelected(var entry)
    signal dismissed()

    // ==================== Public methods ====================
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

    // 当 _hits 变化时,重置 currentIndex 到 0 (跟 query 输入一致)
    on_HitsChanged: reset()

    // ==================== Sizing ====================
    // 高度严格按实际命中数计算,不预留空间:
    //   isEmpty           → 60 (空态文字一行 + padding)
    //   非 isEmpty 1 项   → 1*itemHeight + padding
    //   非 isEmpty N 项   → min(maxSuggestions, N) 项 (含 spacing) + padding
    // 超过 maxSuggestions 才滚动
    implicitWidth: 360
    implicitHeight: {
        if (isEmpty) return 60
        var displayCount = Math.min(maxSuggestions, hitCount)
        // ListView spacing=2, padding 上下各 4 (anchors.margins:4)
        return displayCount * itemHeight + (displayCount - 1) * 2 + 8
    }

    // ==================== HTML 高亮渲染 ====================
    // 把 text + ranges 渲染为 HTML 字符串. ranges 形如 [[start, end], ...]
    // 输出例: '云<b style="color:#0078d4">母</b>效果'
    // 不传 ranges 或 highlightMatches=false → 仅 escape 后返回纯文本
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

    // ==================== Layout ====================
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
            anchors.margins: 4
            visible: !control.isEmpty
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            interactive: true
            keyNavigationEnabled: false  // 自己处理避免冲突
            currentIndex: 0
            highlightMoveDuration: Enums.duration.fast

            model: control._hits
            spacing: 2

            // 滚动条由父 popup 容器决定 (TipPopup / PopupWindowCore 内部已带)

            delegate: Loader {
                width: ListView.view ? ListView.view.width : 0
                height: control.itemHeight
                sourceComponent: itemComponent
                property var hitData: modelData
                property int hitIndex: index
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
