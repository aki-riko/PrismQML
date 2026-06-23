// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// GaussianBlur - Gaussian blur effect 高斯模糊效果
// Replaces Qt5Compat.GraphicalEffects.GaussianBlur 替代
// 
// Usage 用法:
// layer.enabled: true
// layer.effect: GaussianBlur { blur: 0.5 }

MultiEffect {
    id: root
    
    property real radius: Enums.radius.large
    property int samples: 17
    
    blurEnabled: true
    blur: Math.min(1.0, root.radius / 32.0)
    blurMax: 32
}
