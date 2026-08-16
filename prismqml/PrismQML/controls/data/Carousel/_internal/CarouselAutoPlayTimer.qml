// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// CarouselAutoPlayTimer - Advance Carousel while automatic playback is active
// CarouselAutoPlayTimer - 自动播放启用时推进 Carousel
Timer {
    id: autoPlayTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "carouselAutoPlayTimer"
    running: host.autoPlay && host._modelCount > 1
             && !(host.pauseOnHover && host._isHovered)
    repeat: true
    interval: host.interval
    onTriggered: host.next()
}
