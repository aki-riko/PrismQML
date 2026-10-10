// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "_internal"
import "_internal/AppBarDisplayStateResolver.js" as AppBarDisplayStateResolver

// AppBarSeparator - WinUI AppBar command separator 应用栏命令分隔线
// Shares the AppBar display-state machine so a compact host shortens it.
// 复用应用栏显示状态机, 紧凑宿主下自动缩短。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int displayState: Enums.commandBar.appBar_inherit
    property color lineColor: Enums.stateColor.border

    // ==================== Internal Props 内部属性 ====================
    readonly property bool _isAppBarDisplayStateHost: false

    // ==================== Readonly State 只读状态 ====================
    readonly property int resolvedDisplayState: displayState === Enums.commandBar.appBar_inherit
        ? AppBarDisplayStateResolver.resolve(control, Enums) : displayState
    readonly property bool appBarSticky: resolvedDisplayState === Enums.commandBar.appBar_sticky
    readonly property bool appBarCompact: resolvedDisplayState === Enums.commandBar.appBar_compact
    readonly property bool appBarExpanded: resolvedDisplayState === Enums.commandBar.appBar_expanded
    readonly property string appBarStateName: appBarSticky ? "sticky"
        : (appBarCompact ? "compact" : "expanded")

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.commandBarSeparatorWidth
    implicitHeight: appBarCompact ? Enums.controlSize.commandBarButtonSize
        : Enums.controlSize.commandBarButtonSize * 2
    width: implicitWidth
    height: parent && parent.height > 0
        ? Math.min(implicitHeight, parent.height - Enums.spacing.xs) : implicitHeight

    // ==================== Content 内容 ====================
    Separator {
        anchors.centerIn: parent
        type: Enums.separator.vertical
        lineLength: control.height - Enums.spacing.xs
        lineColor: control.lineColor
    }
}
