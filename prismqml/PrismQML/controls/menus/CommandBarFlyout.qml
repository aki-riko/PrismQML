// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal" as MenuInternal

// CommandBarFlyout - Anchored command flyout 锚定命令浮出层
// State machine 状态机: collapsed → mini-expanded → expanded. The flyout always opens as
// its own native popup window, never as an in-window layer (AGENTS.md 4.8).
// 浮出层始终以独立原生弹层窗口打开, 绝不降级为页内弹层。
PopupWindowCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var primaryCommands: []
    property var secondaryCommands: []
    property int type: Enums.commandBar.type_default
    property int iconSize: Enums.iconSize.m
    property int spacing: Enums.spacing.xs
    property bool alwaysExpanded: false
    property int expansionState: Enums.commandBar.flyout_collapsed

    // ==================== Readonly State 只读状态 ====================
    readonly property var _safePrimaryCommands:
        primaryCommands === null || primaryCommands === undefined ? []
        : (typeof primaryCommands.length === "number" ? primaryCommands : [])
    readonly property var _safeSecondaryCommands:
        secondaryCommands === null || secondaryCommands === undefined ? []
        : (typeof secondaryCommands.length === "number" ? secondaryCommands : [])
    readonly property bool _hasSecondaryCommands: _safeSecondaryCommands.length > 0
    readonly property bool fullyExpanded:
        alwaysExpanded || expansionState === Enums.commandBar.flyout_expanded
    readonly property bool expanded: fullyExpanded
        || expansionState === Enums.commandBar.flyout_mini_expanded

    // ==================== Signals 信号 ====================
    signal actionTriggered(int index, var action)
    signal secondaryActionTriggered(int index, var action)

    // ==================== Public Methods 公开方法 ====================
    // Show anchored below the target control 在目标控件下方锚定显示
    function show(targetItem) {
        var target = targetItem || targetControl || parent
        if (target && target.mapToGlobal) openAtControl(target)
    }

    // Hide the flyout 隐藏浮出层
    function hide() { close() }

    // Step forward: collapsed → mini-expanded → expanded 向前推进状态机
    function expand() {
        expansionState = expansionState === Enums.commandBar.flyout_collapsed
            ? Enums.commandBar.flyout_mini_expanded
            : Enums.commandBar.flyout_expanded
    }

    // Step back: expanded → mini-expanded → collapsed 向后回退状态机
    function collapse() {
        expansionState = expansionState === Enums.commandBar.flyout_expanded
            ? Enums.commandBar.flyout_mini_expanded
            : Enums.commandBar.flyout_collapsed
    }

    // Toggle the secondary command row 切换次命令行
    function toggleSecondary() {
        expansionState = expanded
            ? Enums.commandBar.flyout_collapsed
            : Enums.commandBar.flyout_mini_expanded
    }

    // Toggle the labelled state, staying inside the secondary row 在次命令行内切换标签状态
    function toggleExpanded() {
        expansionState = fullyExpanded
            ? Enums.commandBar.flyout_mini_expanded
            : Enums.commandBar.flyout_expanded
    }

    // ==================== Internal Methods 内部方法 ====================
    function _triggerPrimary(index, action) {
        actionTriggered(index, action)
        if (!alwaysExpanded) close()
    }

    function _triggerSecondary(index, action) {
        secondaryActionTriggered(index, action)
        if (!alwaysExpanded) close()
    }

    // ==================== Size 尺寸 ====================
    implicitContentWidth: flyoutSurface.implicitWidth
    implicitContentHeight: flyoutSurface.implicitHeight
    onClosed: expansionState = Enums.commandBar.flyout_collapsed

    // ==================== Content 内容 ====================
    MenuInternal.CommandBarFlyoutSurface {
        id: flyoutSurface
        flyout: control
    }
}
