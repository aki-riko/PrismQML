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
    // Set threshold to 0 for full mask visibility 阈值0全可见
    maskThresholdMin: 0.0
    // Inverted masks must preserve zero-alpha pixels before inversion 反向蒙版必须在反转前保留零透明度像素
    maskSpreadAtMin: root.invert ? 0.0 : 1.0
}
