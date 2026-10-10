// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

pragma Singleton

import QtQuick
import "../.."

// AccessibilityHelper - Accessible role/name resolution 无障碍角色与名称解析
// Consumers pass an Enums.accessibility token and receive the matching Qt
// Accessible enum, so no component re-states the numeric mapping.
// 消费者传入 Enums.accessibility 令牌并取回对应的 Qt Accessible 枚举，
// 因此没有组件需要重复书写数值映射。
QtObject {
    // ==================== Public Methods 公开方法 ====================
    // Map an Enums.accessibility.role_* token onto the Qt Accessible role.
    // 把 Enums.accessibility.role_* 令牌映射为 Qt 无障碍角色。
    function roleValue(role) {
        switch (role) {
        case Enums.accessibility.role_button: return Accessible.Button
        case Enums.accessibility.role_checkbox: return Accessible.CheckBox
        case Enums.accessibility.role_radiobutton: return Accessible.RadioButton
        case Enums.accessibility.role_switch: return Accessible.Switch
        case Enums.accessibility.role_slider: return Accessible.Slider
        case Enums.accessibility.role_textfield: return Accessible.EditableText
        case Enums.accessibility.role_combobox: return Accessible.ComboBox
        case Enums.accessibility.role_list: return Accessible.List
        case Enums.accessibility.role_listitem: return Accessible.ListItem
        case Enums.accessibility.role_tab: return Accessible.PageTab
        case Enums.accessibility.role_tabbar: return Accessible.PageTabList
        case Enums.accessibility.role_menu: return Accessible.PopupMenu
        case Enums.accessibility.role_menuitem: return Accessible.MenuItem
        case Enums.accessibility.role_dialog: return Accessible.Dialog
        case Enums.accessibility.role_progressbar: return Accessible.ProgressBar
        case Enums.accessibility.role_tooltip: return Accessible.ToolTip
        case Enums.accessibility.role_group: return Accessible.Grouping
        case Enums.accessibility.role_pane: return Accessible.Pane
        case Enums.accessibility.role_heading: return Accessible.Heading
        case Enums.accessibility.role_statictext: return Accessible.StaticText
        default: return Accessible.NoRole
        }
    }

    // Split a "Label|Extra detail" accessible name into its primary text.
    // 从「主文本|附加说明」式无障碍名称中取出主文本。
    function namePart(name) {
        var text = name === undefined || name === null ? "" : String(name)
        var separator = text.indexOf("|")
        return separator < 0 ? text : text.slice(0, separator)
    }

    // Build an accessible description from the non-empty parts, so consumers can
    // pass optional hints without producing "undefined" noise in screen readers.
    // 由非空片段拼装无障碍描述，使消费者可传入可选提示而不产生 undefined 噪声。
    function describe(parts) {
        if (parts === undefined || parts === null) return ""
        var collected = []
        for (var index = 0; index < parts.length; index++) {
            var part = parts[index]
            if (part === undefined || part === null) continue
            var text = String(part).trim()
            if (text !== "") collected.push(text)
        }
        return collected.join(". ")
    }

    // Resolve a stable accessible name: an explicit name always wins, otherwise
    // fall back to the visible text and finally to the tooltip.
    // 解析稳定的无障碍名称：显式名称优先，其次可见文本，最后提示文本。
    function resolveName(explicitName, visibleText, toolTipText) {
        var explicit = explicitName === undefined || explicitName === null
            ? "" : String(explicitName).trim()
        if (explicit !== "") return explicit
        var visible = visibleText === undefined || visibleText === null
            ? "" : String(visibleText).trim()
        if (visible !== "") return visible
        return toolTipText === undefined || toolTipText === null
            ? "" : String(toolTipText).trim()
    }
}
