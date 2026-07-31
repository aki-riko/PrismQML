// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../../effects"

// ButtonNeoShadow - Neo hard shadow and shared press transform Neo硬阴影与共享按压变换
NeoShadow {
    id: shadow

    // ==================== Required Props 必需属性 ====================
    required property real pressShift

    // ==================== Internal Props 内部属性 ====================
    property real _animatedPressShift: pressShift

    // Keep the shared transform externally reusable by all button face layers. 保持共享变换供按钮各表面层复用。
    readonly property alias pressTransform: pressTransform

    Behavior on _animatedPressShift {
        NumberAnimation {
            duration: Enums.duration.fast
            easing.type: Easing.OutCubic
        }
    }

    // ==================== Content 内容 ====================
    Translate {
        id: pressTransform
        x: shadow._animatedPressShift
        y: shadow._animatedPressShift
    }
}
