// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import ".."

// TicketPaper - Tiled security-paper texture 平铺防伪票据纸纹
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property color inkColor: Enums.ticket.dividerColor
    property real patternOpacity: Enums.opacityLevel.faint
    property real patternOriginX: 0
    property real patternOriginY: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property real _patternSourceX: -Math.max(0, patternOriginX)
    readonly property real _patternSourceY: -Math.max(0, patternOriginY)

    visible: Enums.isVintageTicket
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
