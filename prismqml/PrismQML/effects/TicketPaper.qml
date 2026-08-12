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

    visible: Enums.isVintageTicket
    opacity: patternOpacity
    clip: true

    // ==================== Content 内容 ====================
    Image {
        id: patternSource

        anchors.fill: parent
        source: Qt.resolvedUrl("_internal/ticket-crosshatch.svg")
        fillMode: Image.Tile
        visible: false
    }

    MultiEffect {
        anchors.fill: parent
        source: patternSource
        colorization: 1
        colorizationColor: control.inkColor
    }
}
