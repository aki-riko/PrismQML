// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ConstantsNeoColors - Neobrutalism source palette 新粗野皮肤原始调色板
QtObject {
    required property bool isDark

    // Background layer: light cream / dark charcoal 背景层：浅色米白 / 深色炭灰
    readonly property color background: isDark ? "#1A1A1A" : "#FAFAF0"
    readonly property color surface: isDark ? "#262626" : "#FFFFFF"
    readonly property color muted: isDark ? "#2E2E2E" : "#F5F5F5"
    // Text: light near-black / dark near-white 文字：浅色近黑 / 深色近白
    readonly property color foreground: isDark ? "#F5F5F0" : "#171717"
    readonly property color secondaryForeground: isDark ? "#A0A0A0" : "#666666"
    // Stroke + hard shadow: light black / dark near-white 描边与硬阴影：浅色黑 / 深色近白
    readonly property color border: isDark ? "#F5F5F0" : "#000000"
    readonly property color shadow: isDark ? "#F5F5F0" : "#000000"
    // Accent and semantic colors brighten in dark mode 深色模式下提亮主色与语义色
    readonly property color primary: isDark ? "#FB923C" : "#F97316"      // Orange 橙
    readonly property color primaryForeground: isDark ? "#1A1A1A" : "#FFFFFF"  // Text on primary 主色文字
    readonly property color success: isDark ? "#22C55E" : "#16A34A"      // Green 绿
    readonly property color danger: isDark ? "#F87171" : "#EF4444"       // Red 红
    readonly property color warning: isDark ? "#FBBF24" : "#F59E0B"      // Amber 琥珀
    readonly property color info: isDark ? "#60A5FA" : "#3B82F6"         // Blue 蓝
}
