// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "_internal"
import "_internal/AppBarDisplayStateResolver.js" as AppBarDisplayStateResolver

// RibbonGroup - Ribbon command group with a bottom caption 功能区命令分组, 底部带分组标题
// Commands are declared directly inside the group and laid out in one row.
// 命令直接声明在分组内, 由分组按一行排布。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string title: ""
    property int displayState: Enums.commandBar.appBar_inherit
    default property alias commands: commandRow.data

    // ==================== Internal Props 内部属性 ====================
    readonly property bool _isAppBarDisplayStateHost: displayState !== Enums.commandBar.appBar_inherit
    readonly property int _horizontalPadding: Enums.spacing.m
    readonly property int _captionHeight: Enums.typography.captionCompact + Enums.spacing.xs

    // ==================== Readonly State 只读状态 ====================
    readonly property bool isRibbonGroup: true  // Ribbon discovery marker 供功能区识别的标记
    readonly property int resolvedDisplayState: displayState === Enums.commandBar.appBar_inherit
        ? AppBarDisplayStateResolver.resolve(control, Enums) : displayState
    readonly property bool appBarSticky: resolvedDisplayState === Enums.commandBar.appBar_sticky
    readonly property bool appBarCompact: resolvedDisplayState === Enums.commandBar.appBar_compact
    readonly property bool appBarExpanded: resolvedDisplayState === Enums.commandBar.appBar_expanded
    readonly property string appBarStateName: appBarSticky ? "sticky"
        : (appBarCompact ? "compact" : "expanded")
    readonly property bool captionVisible: !appBarCompact && title !== ""
    // Only the trailing group of a tab drops its divider. 仅标签页内最后一个分组不画分隔线。
    // When the parent is not a RibbonTab there is no ordering contract, so keep it set.
    // 父级不是标签页时没有次序契约, 因此保持绘制。
    readonly property bool _isLastGroup: {
        var parentRow = control.parent
        if (!parentRow || parentRow._groupRevision === undefined || !parentRow.children)
            return true
        return parentRow.children[parentRow.children.length - 1] === control
    }

    // ==================== Size 尺寸 ====================
    width: implicitWidth
    height: parent ? parent.height : implicitHeight
    implicitWidth: commandRow.implicitWidth + _horizontalPadding * 2
        + (groupDivider.visible ? groupDivider.width : 0)
    implicitHeight: _captionHeight + commandRow.implicitHeight

    // ==================== Content 内容 ====================
    Row {
        id: commandRow

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.leftMargin: control._horizontalPadding
        height: Math.max(0, control.height - control._captionHeight)
        spacing: Enums.spacing.xs
    }

    Label {
        id: captionLabel

        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: Enums.spacing.xxs
        type: Enums.label.type_caption
        text: control.title
        customTextColor: Enums.secondaryForeground
        visible: control.captionVisible
    }

    Separator {
        id: groupDivider

        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        type: Enums.separator.vertical
        lineLength: control.height - Enums.spacing.s
        lineColor: Enums.stateColor.divider
        visible: !control._isLastGroup
    }
}
