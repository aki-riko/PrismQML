// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "ComboBoxMethods.js" as ComboBoxMethods

// ComboBoxSearchState - Type-to-search state for the editable ComboBox 可编辑下拉框输入即搜索状态
// The editable input doubles as the search field: typing narrows the candidate list,
// and a visible row is mapped back to its source model index so filtering never
// renumbers icons, item data, enabled flags or the activated() index.
// 可编辑输入框同时充当搜索框: 输入即收窄候选列表; 可见行会映射回源模型下标,
// 因此过滤不会改变图标、项目数据、禁用态与 activated() 下标。
QtObject {
    id: state

    // ==================== Required Props 必需属性 ====================
    required property var model
    // The candidate surface exists from the open call until the close animation ends.
    // 候选表面从展开调用起存在, 直到关闭动画结束。
    required property bool expanded
    // Only the default candidate row maps a visible row back to its source model index,
    // so a custom popupDelegate keeps the full list instead of being renumbered.
    // 只有默认候选行会把可见行映射回源模型下标, 因此自定义 popupDelegate 保持完整列表,
    // 不会被重新编号。
    required property bool mapsSourceIndex

    // ==================== Public Props 公开属性 ====================
    property string text: ""

    // ==================== Readonly State 只读状态 ====================
    readonly property var filter: ComboBoxMethods.filterModel(model, text)
    // A free-form value that matches nothing keeps the full list, so an editable
    // control that accepts arbitrary text never shows an empty candidate list.
    // 未命中任何候选的自由文本保持完整列表, 因此允许任意输入的可编辑控件不会出现空候选列表。
    readonly property bool active: mapsSourceIndex && text !== ""
        && filter.indices.length > 0
    readonly property var visibleModel: active ? filter.items : (model ? model : [])
    readonly property var visibleIndices: active ? filter.indices : []

    // ==================== Signals 信号 ====================
    signal openRequested()

    // ==================== Public Methods 公开方法 ====================
    // Drive the filter from the editable input and expand the list once the typed
    // text actually narrows the candidates.
    // 由可编辑输入框驱动过滤; 输入真正收窄候选时展开列表。
    function apply(value) {
        text = value
        if (!expanded && active) openRequested()
    }

    // Map a visible row back to its source model index. 把可见行映射回源模型下标。
    function sourceIndex(visibleIndex) {
        if (!active || visibleIndex < 0 || visibleIndex >= visibleIndices.length)
            return visibleIndex
        return visibleIndices[visibleIndex]
    }

    // ==================== Content 内容 ====================
    // A dismissed list forgets the last query: the query outlives the close animation
    // so the fading list cannot jump back to the full model, and is dropped once the
    // candidate surface is really gone.
    // 列表收起后丢弃上一次查询: 查询活过关闭动画, 收起中的列表因此不会跳回全量,
    // 候选表面真正消失后才丢弃。
    onExpandedChanged: if (!expanded) text = ""
}
