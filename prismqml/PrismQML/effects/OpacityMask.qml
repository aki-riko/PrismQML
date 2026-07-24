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
    // Map the full mask alpha range so antialiased edges survive inversion 映射完整蒙版透明度范围，使反向遮罩保留抗锯齿边缘
    maskThresholdMin: 0.5
    maskSpreadAtMin: 1.0
}
