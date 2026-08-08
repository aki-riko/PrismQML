// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// CloseRippleDissolve - Shared item exit using the window-close ripple 使用窗口关闭涟漪的共享项目退场
Item {
    id: effect

    // ==================== Required Props 必需属性 ====================
    required property Item sourceItem

    // ==================== Readonly State 只读状态 ====================
    readonly property bool running: _running

    // ==================== Internal Props 内部属性 ====================
    property bool _running: false
    property real _dissolveProgress: Enums.opacityLevel.invisible

    // ==================== Signals 信号 ====================
    signal finished()

    // ==================== Public Methods 公开方法 ====================
    function start() {
        if (effect._running)
            return
        rippleAnimation.stop()
        effect._dissolveProgress = Enums.opacityLevel.invisible
        effect._running = true
        effect.sourceItem.layer.effect = rippleEffectComponent
        effect.sourceItem.layer.enabled = true
        rippleAnimation.start()
    }

    function stop() {
        rippleAnimation.stop()
        effect._disableLayer()
        effect._running = false
        effect._dissolveProgress = Enums.opacityLevel.invisible
    }

    // ==================== Internal Methods 内部方法 ====================
    function _disableLayer() {
        if (!effect.sourceItem)
            return
        effect.sourceItem.layer.enabled = false
        effect.sourceItem.layer.effect = null
    }

    visible: _running
    Component.onDestruction: effect.stop()

    SequentialAnimation {
        id: rippleAnimation

        NumberAnimation {
            target: effect
            property: "_dissolveProgress"
            to: Enums.opacityLevel.visible
            duration: Enums.windowCloseMetrics.rippleDuration
            easing.type: Easing.OutQuad
        }

        ScriptAction {
            script: {
                effect._disableLayer()
                effect._running = false
                effect.finished()
            }
        }
    }

    // Install the same shader as the native window close effect on demand.
    // 按需把与原生窗口关闭相同的着色器安装到源项目。
    Component {
        id: rippleEffectComponent

        CloseRippleFrame {
            progress: effect._dissolveProgress
        }
    }
}
