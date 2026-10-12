// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ConstantsNeumorphismColors - Neumorphism source palette 新拟态皮肤原始调色板
QtObject {
    required property bool isDark

    // Surface and canvas intentionally share a base color; depth comes from paired soft shadows.
    // 表面与画布有意保持同色，立体感由双向软阴影产生。
    readonly property color background: isDark ? "#252B35" : "#E4EBF3"
    readonly property color surface: isDark ? "#252B35" : "#E4EBF3"
    readonly property color muted: isDark ? "#303947" : "#D7E0EB"
    readonly property color hover: isDark ? "#2D3541" : "#DCE5EF"
    readonly property color pressed: isDark ? "#202731" : "#CDD8E5"
    readonly property color disabledSurface: isDark ? "#2A313C" : "#DDE5EE"
    readonly property color divider: isDark ? "#465365" : "#C2CCD9"
    readonly property color indicator: isDark ? "#7F8DA1" : "#7A899D"
    readonly property color indicatorHover: isDark ? "#AAB7C8" : "#596A80"
    readonly property color foreground: isDark ? "#E8EEF7" : "#27364A"
    readonly property color secondaryForeground: isDark ? "#AAB7C8" : "#66758A"
    readonly property color disabledForeground: isDark ? "#697687" : "#9BA8B8"
    readonly property color shadowDark: isDark ? "#171C24" : "#B7C2D0"
    readonly property color shadowLight: isDark ? "#3E4A5B" : "#FFFFFF"
    readonly property color primary: isDark ? "#8CB4FF" : "#3867D6"
    readonly property color primaryForeground: "#FFFFFF"
    readonly property color selected: isDark ? "#344159" : "#CCD9EF"
    readonly property color selectedHover: isDark ? "#3A4A64" : "#C2D2EC"
    readonly property color success: isDark ? "#72D6A0" : "#238B64"
    readonly property color danger: isDark ? "#FF9A9A" : "#C94B58"
    readonly property color warning: isDark ? "#F2C879" : "#A86F1E"
    readonly property color info: isDark ? "#82C8E8" : "#397A9A"
}
