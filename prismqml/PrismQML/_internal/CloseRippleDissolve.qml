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

    // ==================== Public Props 公开属性 ====================
    property bool reverse: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool running: _running
    readonly property real _dissolveProgress: rippleAnimator.progress

    // ==================== Internal Props 内部属性 ====================
    property bool _running: false

    // ==================== Signals 信号 ====================
    signal finished()

    // ==================== Public Methods 公开方法 ====================
    function start() {
        if (effect._running)
            return
        rippleAnimator.reverse = effect.reverse
        rippleAnimator.prepare()
        effect._running = true
        effect.sourceItem.layer.effect = rippleEffectComponent
        effect.sourceItem.layer.enabled = true
        rippleAnimator.startPrepared()
    }

    function stop() {
        rippleAnimator.stop()
        effect._disableLayer()
        effect._running = false
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

    CloseRippleAnimator {
        id: rippleAnimator

        onFinished: {
            effect._disableLayer()
            effect._running = false
            effect.finished()
        }
    }

    // Install the same shader as the native window close effect on demand.
    // 按需把与原生窗口关闭相同的着色器安装到源项目。
    Component {
        id: rippleEffectComponent

        CloseRippleFrame {
            progress: rippleAnimator.progress
        }
    }
}
