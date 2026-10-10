// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "_internal"
import "_internal/AppBarDisplayStateResolver.js" as AppBarDisplayStateResolver

// RibbonTab - Ribbon tab page owning one row of groups 功能区标签页, 承载一行功能分组
// Declared as a RibbonBar child; RibbonBar assigns tabIndex/selected at runtime.
// 作为功能区子项声明; 序号与选中态由功能区在运行时写入。
Row {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string title: ""
    property string key: ""
    property string icon: ""
    property bool selected: false
    property int tabIndex: -1
    property int displayState: Enums.commandBar.appBar_inherit

    // ==================== Internal Props 内部属性 ====================
    // A host only while this tab pins an explicit state. 仅当标签页固定显式状态时才作为宿主。
    readonly property bool _isAppBarDisplayStateHost: displayState !== Enums.commandBar.appBar_inherit
    // Group list changes are not observable through children, so bump a revision.
    // 分组列表变化不可通过 children 观测, 因此递增修订号。
    property int _groupRevision: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property bool isRibbonTab: true  // RibbonBar tab discovery marker 供功能区识别标签页的标记
    readonly property int resolvedDisplayState: displayState === Enums.commandBar.appBar_inherit
        ? AppBarDisplayStateResolver.resolve(control, Enums) : displayState
    readonly property bool appBarSticky: resolvedDisplayState === Enums.commandBar.appBar_sticky
    readonly property bool appBarCompact: resolvedDisplayState === Enums.commandBar.appBar_compact
    readonly property bool appBarExpanded: resolvedDisplayState === Enums.commandBar.appBar_expanded
    readonly property string appBarStateName: appBarSticky ? "sticky"
        : (appBarCompact ? "compact" : "expanded")

    // ==================== Size 尺寸 ====================
    width: parent ? parent.width : implicitWidth
    height: parent ? parent.height : implicitHeight
    spacing: Enums.spacing.none
    visible: selected

    onChildrenChanged: _groupRevision++
}
