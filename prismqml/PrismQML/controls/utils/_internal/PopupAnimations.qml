// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import QtQuick

// PopupAnimations - Popup entrance and exit animations 弹层进出场动画
// Keeps visual timing separate from PopupWindowCore lifecycle logic 将视觉时序与生命周期逻辑分离
Item {
    id: animations

    // ==================== Required Props 必需属性 ====================
    required property Item control
    required property Item surface
    required property bool usesControlsPopup
    required property var inlinePopup
    required property var popupWindow

    // ==================== Public Props 公开属性 ====================
    property alias showAnimation: showAnim
    property alias hideAnimation: hideAnim

    // ==================== Content 内容 ====================
    ParallelAnimation {
        id: showAnim

        NumberAnimation {
            target: animations.surface
            property: "opacity"
            from: 0
            to: 1
            duration: Enums.popupMetrics.showOpacityDuration
            easing.type: Easing.OutQuad
        }
        NumberAnimation {
            target: animations.control
            property: "_clipHeight"
            from: 0
            to: animations.control.popupHeight
            duration: Enums.popupMetrics.showRevealDuration
            easing.type: Easing.OutCubic
        }
    }

    SequentialAnimation {
        id: hideAnim

        ParallelAnimation {
            NumberAnimation {
                target: animations.surface
                property: "opacity"
                from: 1
                to: 0
                duration: Enums.popupMetrics.hideOpacityDuration
                easing.type: Easing.InQuad
            }
            NumberAnimation {
                target: animations.control
                property: "_clipHeight"
                from: animations.control.popupHeight
                to: 0
                duration: Enums.popupMetrics.hideRevealDuration
                easing.type: Easing.InCubic
            }
        }

        ScriptAction {
            script: {
                if (animations.usesControlsPopup) animations.inlinePopup.close()
                else if (animations.popupWindow) animations.popupWindow.hide()
                animations.control.isClosing = false
                animations.control._clipHeight = 0
            }
        }
    }
}
