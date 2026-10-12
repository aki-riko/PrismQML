// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ConstantsTicketColors - Vintage ticket source palette 复古票据皮肤原始调色板
QtObject {
    required property bool isDark

    // Warm paper, aged ink and stamp colors are the single source of truth for vintage_ticket.
    // 暖纸、旧油墨与印章色是 vintage_ticket 皮肤的唯一配色真相源。
    readonly property color background: isDark ? "#1D1A17" : "#E9E1D2"
    readonly property color surface: isDark ? "#28231E" : "#F8F3E8"
    readonly property color muted: isDark ? "#342E27" : "#EEE6D8"
    readonly property color foreground: isDark ? "#EDE3D2" : "#2B211A"
    readonly property color secondaryForeground: isDark ? "#B9AB98" : "#74685B"
    readonly property color disabledForeground: isDark ? "#766B60" : "#A79B8B"
    readonly property color border: isDark ? "#B4A48E" : "#5A4637"
    readonly property color divider: isDark ? "#776A5B" : "#B8AA96"
    readonly property color primary: isDark ? "#C6A66B" : "#5A3D2B"
    readonly property color primaryForeground: isDark ? "#1D1A17" : "#FFF9EE"
    readonly property color success: isDark ? "#68A77C" : "#267451"
    readonly property color danger: isDark ? "#D37B72" : "#A33E36"
    readonly property color warning: isDark ? "#C9A45D" : "#91651F"
    readonly property color info: isDark ? "#88A9AE" : "#416C73"
}
