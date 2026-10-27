// ButtonGlow - Bloom halo behind a glow button face 泛光按钮面背后的光晕
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ButtonGlow - Stacked translucent discs approximating a soft bloom 叠加半透明圆盘近似柔和泛光
//
// Rendered as concentric translucent rounded rectangles instead of a shader
// blur. Field measurement on a real D3D11 window showed RectangularShadow and
// MultiEffect blur draw nothing behind this surface, while stacked translucent
// rectangles are visible; StepperHalo uses the same technique for its halo.
// 用同心半透明圆角矩形叠加渲染，而不是着色器模糊。真实 D3D11 窗口实测显示该表面
// 背后的 RectangularShadow 与 MultiEffect 模糊均无绘制，而叠加半透明矩形可见；
// StepperHalo 的光晕采用同一技术。
//
// The discs are centered on the face and each one is larger than the face, so
// the bloom reads as an outward falloff and no item needs a negative margin.
// 各圆盘以按钮面为中心且每层都比面大, 因此泛光呈向外衰减, 无需负边距。
//
// Only the pulse runs a loop, and only while the host can actually show a bloom;
// a burst of glowing buttons therefore costs one loop per visible instance and
// zero loops in disabled, loading, countdown, or reduced-motion states.
// 只有呼吸动画运行循环, 且仅在宿主真能显示泛光时运行; 因此一组泛光按钮的动画开销与
// 可见实例数成正比, 禁用/加载/倒计时/减少动态效果状态下为零。
Item {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property var button

    // ==================== Readonly State 只读状态 ====================
    readonly property var _skin: button.effectiveSkinContext
    readonly property var _tokens: _skin.button
    // The bloom keeps the painted face hue and only modulates its alpha. 泛光沿用
    // 按钮面已绘制色相, 仅调制其透明度。
    readonly property color _haloColor: button._effectiveBgColor
    readonly property real _spread: _tokens.glowSpread
    readonly property int _layerCount: _tokens.glowLayerCount
    // Disc geometry is derived from the face, so a pill shape keeps a pill bloom.
    // 圆盘几何由按钮面派生, 因此药丸形状得到药丸形泛光。
    readonly property real _faceWidth: button.width
    readonly property real _faceHeight: button.height
    readonly property real _faceRadius: button.radius
    // Pulse only while the host can actually show a bloom. A hidden window must not
    // keep animating: Qt still drives the animation clock for invisible windows and
    // the pulse would wake the render thread for nothing. 仅当宿主真能显示泛光时
    // 呼吸。隐藏窗口不得继续动画: Qt 对不可见窗口仍驱动动画时钟, 呼吸会白白唤醒
    // 渲染线程。
    readonly property bool _windowShown: {
        var hostWindow = root.Window.window
        return hostWindow === null || hostWindow === undefined
            || hostWindow.visible === true
    }
    readonly property bool animated: button._styleEffectiveEnabled
        && !button._countdownActive
        && !_skin.reduceMotion
        && root._windowShown && root._spread > 0
    readonly property real _stateStrength: !button._styleEffectiveEnabled
        ? _tokens.glowDisabledStrength
        : (button.pressed
           ? _tokens.glowPressedStrength
           : (button._touchActive ? _tokens.glowHoverStrength : 1.0))

    // ==================== Internal Props 内部属性 ====================
    property real _breath: 1.0

    // The module is created imperatively by ButtonSurface, so it must anchor
    // itself to the button it was handed and sit behind every face layer.
    // 本模块由 ButtonSurface 以命令式创建, 因此必须自行锚定到传入的按钮, 并位于所有
    // 按钮面图层之下。
    parent: button
    anchors.fill: parent
    z: _skin.zIndex.background

    // ==================== Content 内容 ====================
    Repeater {
        model: root._layerCount

        Rectangle {
            // Layer 0 is the outermost disc and is painted first, so the faintest
            // halo sits at the back and the brightest disc ends up on top nearest
            // the face. 第 0 层是最外层并最先绘制, 因此最暗的光晕在最背后, 最亮的圆盘
            // 最后绘制并贴近按钮面。
            readonly property int _layerOrder: root._layerCount - 1 - index
            readonly property real _growth:
                root._spread * (_layerOrder + 1) / root._layerCount

            anchors.centerIn: parent
            width: root._faceWidth + _growth * 2
            height: root._faceHeight + _growth * 2
            radius: root._faceRadius + _growth
            color: root._haloColor
            opacity: root._tokens.glowLayerOpacity
                * (1 - _layerOrder * root._tokens.glowLayerFalloff)
                * root._breath * root._stateStrength
        }
    }

    SequentialAnimation {
        running: root.animated
        loops: Animation.Infinite
        onStopped: root._breath = 1.0

        NumberAnimation {
            target: root
            property: "_breath"
            from: root._tokens.glowPulseMin
            to: root._tokens.glowPulseMax
            duration: root._tokens.glowBreatheDuration
            easing.type: Easing.InOutSine
        }
        NumberAnimation {
            target: root
            property: "_breath"
            from: root._tokens.glowPulseMax
            to: root._tokens.glowPulseMin
            duration: root._tokens.glowBreatheDuration
            easing.type: Easing.InOutSine
        }
    }
}
