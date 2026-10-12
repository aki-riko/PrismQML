// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ConstantsColorPickerGradient - Picker gradient stops 颜色选择器渐变停靠点
QtObject {
    // Hue slider stops 色相滑块渐变停靠点
    readonly property real huePos0: 0.0
    readonly property real huePos1: 0.166
    readonly property real huePos2: 0.333
    readonly property real huePos3: 0.5
    readonly property real huePos4: 0.666
    readonly property real huePos5: 0.833
    readonly property real huePos6: 1.0

    readonly property color hueColor0: "#ff0000"
    readonly property color hueColor1: "#ffff00"
    readonly property color hueColor2: "#00ff00"
    readonly property color hueColor3: "#00ffff"
    readonly property color hueColor4: "#0000ff"
    readonly property color hueColor5: "#ff00ff"
    readonly property color hueColor6: "#ff0000"

    // Fixed lightness palette 固定明度色板
    readonly property color lightnessDark: "#000000"
    readonly property color lightnessMid: "#808080"
    readonly property color lightnessLight: "#ffffff"
}
