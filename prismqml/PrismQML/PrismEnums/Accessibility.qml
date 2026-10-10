// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Accessibility - Accessibility roles and states 无障碍角色与状态
// Usage 使用方式: Enums.accessibility.role_button, Enums.accessibility.state_expanded
// Mirrors the accessibility roles that Fluent exposes on every interactive
// surface. 对齐 Fluent 在每个可交互表面上暴露的无障碍角色。
QtObject {
    // ==================== Roles 角色 ====================
    readonly property int role_none: 0
    readonly property int role_button: 1
    readonly property int role_checkbox: 2
    readonly property int role_radiobutton: 3
    readonly property int role_switch: 4
    readonly property int role_slider: 5
    readonly property int role_textfield: 6
    readonly property int role_combobox: 7
    readonly property int role_list: 8
    readonly property int role_listitem: 9
    readonly property int role_tab: 10
    readonly property int role_tabbar: 11
    readonly property int role_menu: 12
    readonly property int role_menuitem: 13
    readonly property int role_dialog: 14
    readonly property int role_progressbar: 15
    readonly property int role_tooltip: 16
    readonly property int role_group: 17
    readonly property int role_pane: 18
    readonly property int role_heading: 19
    readonly property int role_statictext: 20

    // ==================== States 状态 ====================
    readonly property int state_none: 0
    readonly property int state_expanded: 1
    readonly property int state_collapsed: 2
    readonly property int state_selected: 3
    readonly property int state_busy: 4
    readonly property int state_invalid: 5

    // ==================== Live Region 实时区域 ====================
    // Polite announcements queue behind the user's current action; assertive
    // ones interrupt it. 礼貌播报排队等待用户当前操作，强硬播报会打断。
    readonly property int live_off: 0
    readonly property int live_polite: 1
    readonly property int live_assertive: 2
}
