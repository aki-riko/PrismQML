// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// ColorOverlay - Color overlay effect 颜色叠加效果
// Replaces Qt5Compat.GraphicalEffects.ColorOverlay 替代
// Uses brightness + colorization to achieve color replacement 使用亮度+着色实现颜色替换

MultiEffect {
    id: root
    property color color: "white"
    
    // First brighten to white, then colorize 先提亮到白色，再着色
    // This ensures dark source images (like #212121 SVGs) are properly colored 确保深色源图像（如 #212121 的 SVG）能正确着色

    brightness: 1.0
    colorization: 1.0
    colorizationColor: root.color
}
