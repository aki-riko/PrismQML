// ButtonGlow - Bloom halo behind a glow button face 泛光按钮面背后的光晕
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."

// ButtonGlow - SDF bloom halo behind a glow button face 泛光按钮面背后的 SDF 光晕
//
// The bloom is one RectangularShadow, which is the repo's mandated first choice for
// rectangular surfaces: Qt 6.9+ renders it from a signed-distance field with no
// offscreen layer (AGENTS.md 6.2). It produces a genuinely smooth falloff, unlike
// stacked translucent rectangles, which band on a real display.
// 光晕由单个 RectangularShadow 绘制, 这是仓库对矩形表面规定的首选方案: Qt 6.9+
// 用有符号距离场渲染, 无离屏图层 (AGENTS.md 6.2)。它能产出真正平滑的衰减, 而叠加
// 半透明矩形在真实显示器上会出现可见色带。
//
// The breathing pulse animates only the shadow colour's alpha and the item opacity;
// the geometry stays fixed, so a pulse never re-lays-out or re-rasterizes the face.
// 呼吸脉冲只动画阴影色的 alpha 与项目不透明度; 几何保持不变, 因此呼吸不会触发
// 按钮面的重新布局或重新栅格化。
//
// The halo hue follows the accent colour rather than the resolved face, so a pressed
// or disabled face never shifts the bloom to a muddy in-between colour.
// 光晕色相跟随主色而不是已解析面色, 因此按压或禁用态不会让泛光偏成浑浊的中间色。
Item {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property var button

    // ==================== Readonly State 只读状态 ====================
    readonly property var _skin: button.effectiveSkinContext
    readonly property var _tokens: _skin.button
    // Only the strongest visual signatures are allowed to keep a bloom: ticket paper
    // has zero elevation by design, so it reports a zero spread and the halo is not
    // created at all. 只有允许悬浮的设计语言保留泛光: 票据纸面按设计零悬浮, 因此其
    // 外扩量为 0, 光晕根本不会被创建。
    readonly property real _spread: _tokens.glowSpread
    // The bloom follows the resolved face colour, not the raw accent: a disabled
    // face is neutral grey, and a blue halo around a grey face reads as a rendering
    // bug rather than as a dimmed light.
    // 泛光跟随已解析的面色而不是原始主色: 禁用面是中性灰, 灰面配蓝色光晕会读作渲染
    // 缺陷而不是变暗的灯光。
    readonly property color _haloColor: button._effectiveBgColor
    // Pulse only while the host can actually show a bloom. A hidden window must not
    // keep animating: Qt still drives the animation clock for invisible windows.
    // 仅当宿主真能显示泛光时呼吸。隐藏窗口不得继续动画: Qt 对不可见窗口仍驱动动画
    // 时钟。
    readonly property bool _windowShown: {
        var hostWindow = root.Window.window
        return hostWindow === null || hostWindow === undefined
            || hostWindow.visible === true
    }
    readonly property bool animated: button._styleEffectiveEnabled
        && !button._countdownActive
        && !_skin.reduceMotion
        && root._windowShown && root._spread > 0
    // Pointer states modulate the resting alpha: hover opens the bloom, press pulls
    // it in, and a disabled/loading face keeps a faint static ember.
    // 指针状态调制静息 alpha: 悬浮发散, 按压收敛, 禁用/加载态保留微弱静态余辉。
    readonly property real _stateStrength: !button._styleEffectiveEnabled
        ? _tokens.glowDisabledStrength
        : (button.pressed
           ? _tokens.glowPressedStrength
           : (button._touchActive ? _tokens.glowHoverStrength : 1.0))

    // ==================== Internal Props 内部属性 ====================
    property real _breath: 1.0

    // The module is created imperatively by ButtonSurface, so it anchors itself to
    // the button it was handed and sits behind every face layer.
    // 本模块由 ButtonSurface 以命令式创建, 因此自行锚定到传入的按钮, 并位于所有按钮
    // 面图层之下。
    parent: button
    anchors.fill: parent
    z: _skin.zIndex.background

    // ==================== Content 内容 ====================
    // One SDF shadow carries the whole bloom: blur decides the falloff width and
    // the colour alpha decides its strength.
    // 整圈泛光由单个 SDF 阴影承载: blur 决定衰减宽度, 颜色 alpha 决定强度。
    RectangularShadow {
        anchors.fill: parent
        anchors.margins: -root._spread
        radius: root.button.radius + root._spread
        color: Qt.rgba(
            root._haloColor.r, root._haloColor.g, root._haloColor.b,
            root._tokens.glowHaloAlpha * root._breath * root._stateStrength)
        blur: root._tokens.glowBlur
        spread: root._spread
        offset.x: 0
        offset.y: 0
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
