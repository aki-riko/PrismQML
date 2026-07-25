// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// OpacityMask - Opacity mask effect 透明度遮罩
// Replaces Qt5Compat.GraphicalEffects.OpacityMask 替代Qt5Compat
// 
// Usage 1 - as layer.effect 作为layer.effect使用:
// layer.enabled: true
// layer.effect: OpacityMask { mask: maskItem }
//
// Usage 2 - as standalone component 作为独立组件使用:
// OpacityMask { source: imageItem; mask: maskItem }

MultiEffect {
    id: root

    // ==================== Public Props 公开属性 ====================
    property var mask: null
    property bool invert: false

    // ==================== Content 内容 ====================
    // Only enable when mask exists 仅有mask时启用
    maskEnabled: root.mask !== null
    maskSource: root.mask
    maskInverted: root.invert
    // Keep regular masks at Qt's default threshold; inverted spotlight masks need the midpoint mapping
    // 普通蒙版保留 Qt 默认阈值；仅反向聚光蒙版使用中点映射
    maskThresholdMin: root.invert ? 0.5 : 0.0
    maskSpreadAtMin: 1.0
}
