// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ConstantsColorPalette - Picker color swatches 颜色选择器色板
QtObject {
    readonly property color automaticColor: Qt.rgba(0, 0, 0, 1)

    // Theme colors (10 columns x 6 rows) 主题色
    readonly property var themeColors: [
        // Row 1 第一行
        "#ffffff", "#000000", "#e7e6e6", "#44546a", "#4472c4", "#ed7d31", "#a5a5a5", "#ffc000", "#5b9bd5", "#70ad47",
        // Row 2 第二行
        "#f2f2f2", "#7f7f7f", "#d0cece", "#d6dce4", "#d9e2f3", "#fbe5d5", "#ededed", "#fff2cc", "#deebf6", "#e2efd9",
        // Row 3 第三行
        "#d8d8d8", "#595959", "#aeabab", "#adb9ca", "#b4c6e7", "#f7cbac", "#dbdbdb", "#ffe599", "#bdd7ee", "#c5e0b3",
        // Row 4 第四行
        "#bfbfbf", "#3f3f3f", "#757070", "#8496b0", "#8eaadb", "#f4b183", "#c9c9c9", "#ffd966", "#9cc3e5", "#a8d08d",
        // Row 5 第五行
        "#a5a5a5", "#262626", "#3a3838", "#323f4f", "#2f5496", "#c55a11", "#7b7b7b", "#bf9000", "#2e75b5", "#538135",
        // Row 6 第六行
        "#7f7f7f", "#0c0c0c", "#171616", "#222a35", "#1f3864", "#833c0b", "#525252", "#7f6000", "#1e4e79", "#375623"
    ]

    // Standard colors (10 colors) 标准色
    readonly property var standardColors: [
        "#c00000", "#ff0000", "#ffc000", "#ffff00", "#92d050",
        "#00b050", "#00b0f0", "#0070c0", "#002060", "#7030a0"
    ]
}
