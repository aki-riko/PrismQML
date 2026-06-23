// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import ".."

// Shadow - Unified shadow effect component 统一阴影效果组件
// Based on Qt6 MultiEffect, replaces Qt5Compat.GraphicalEffects.DropShadow
// 
// Usage 用法:
// layer.enabled: true
// layer.effect: Shadow { blur: Enums.shadow.level4.blurNormalized; color: Enums.shadow.level4.color }

MultiEffect {
    id: root
    
    // ==================== 公开属性 ====================
    // blur 使用 0-1 的归一化值（MultiEffect 要求）
    property real blur: Enums.shadow.level4.blurNormalized
    property color color: Enums.shadow.level4.color
    property real radius: Enums.radius.large
    property int samples: Enums.shadow.level4.samples
    property real horizontalOffset: 0
    property real verticalOffset: Enums.shadow.level4.offset
    property real spread: 0.0
    
    // ==================== MultiEffect映射 ====================
    shadowEnabled: true
    shadowColor: root.color
    shadowBlur: root.blur
    shadowHorizontalOffset: root.horizontalOffset
    shadowVerticalOffset: root.verticalOffset
    shadowScale: 1.0 + root.spread
}
