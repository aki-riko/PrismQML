// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import ".."
import "../SkinResolver.js" as SkinResolver

// TicketPaper - Tiled security-paper texture 平铺防伪票据纸纹
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Ordinary children find their nearest scope automatically. Reparented
    // popup/dialog surfaces may pass their captured context explicitly.
    // 普通子项自动查找最近范围；跨窗口重挂载的弹层和对话框可显式传入已捕获上下文。
    property var skinContext: null
    property color inkColor: effectiveSkinContext.ticket.dividerColor
    property real patternOpacity: effectiveSkinContext.opacityLevel.faint
    property real patternOriginX: 0
    property real patternOriginY: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property var effectiveSkinContext:
        skinContext || _nearestSkinContext || Enums
    readonly property real _patternSourceX: -Math.max(0, patternOriginX)
    readonly property real _patternSourceY: -Math.max(0, patternOriginY)

    // ==================== Internal Props 内部属性 ====================
    readonly property var _nearestSkinContext: skinContext
        ? null : SkinResolver.nearestContext(parent)

    visible: effectiveSkinContext.isVintageTicket
    opacity: patternOpacity
    clip: true

    // ==================== Content 内容 ====================
    Item {
        id: patternSource

        anchors.fill: parent
        visible: false
        clip: true

        Image {
            x: control._patternSourceX
            y: control._patternSourceY
            width: patternSource.width - x
            height: patternSource.height - y
            source: Qt.resolvedUrl("_internal/ticket-crosshatch.svg")
            fillMode: Image.Tile
        }
    }

    MultiEffect {
        anchors.fill: parent
        source: patternSource
        colorization: 1
        colorizationColor: control.inkColor
    }
}
