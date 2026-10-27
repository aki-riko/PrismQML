// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import ".."

// GlowHalo - Soft bloom halo around an arbitrary rectangular target 环绕任意矩形目标的柔和泛光
//
// A reusable decoration, not a button feature: it attaches to any rectangular item
// and paints a bloom behind it. Consumers opt in through their own public `glow`
// property (`Enums.glow.glow_none` / `glow_accent`) and provide the halo colour,
// because only the consumer knows what surface it painted.
// 可复用的装饰而非按钮功能: 它可附着到任意矩形项并在其背后绘制泛光。使用者通过各自的
// 公开 `glow` 属性(`Enums.glow.glow_none` / `glow_accent`)启用并提供光晕颜色, 因为只有
// 使用者知道自己画了什么表面。
//
// The bloom is one RectangularShadow, the repo's mandated first choice for
// rectangular surfaces: Qt 6.9+ renders it from a signed-distance field with no
// offscreen layer (AGENTS.md 6.2), and it produces a genuinely smooth falloff.
// 光晕由单个 RectangularShadow 绘制, 这是仓库对矩形表面规定的首选方案: Qt 6.9+
// 用有符号距离场渲染且无离屏图层 (AGENTS.md 6.2), 衰减真正平滑。
//
// Geometry is fixed so a pulse never re-lays-out the target; only the shadow
// colour's alpha breathes. 几何保持不变, 呼吸不触发目标重新布局; 只有阴影色 alpha
// 参与动画。
//
// Usage 用法:
//   GlowHalo { target: myRect; haloColor: myRect.color; active: hovered }
Item {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property Item target              // Rectangular item to bloom around 要环绕的矩形项

    // ==================== Public Props 公开属性 ====================
    property color haloColor: Enums.accentColor  // Supplied by the consumer 由使用者提供
    property var tokens: Enums.glow              // Token set; a scope may override 令牌集; 皮肤范围可覆盖
    property bool active: true                    // Whether any bloom is shown 是否显示泛光
    property bool pulseEnabled: true              // Allow the breathing pulse 允许呼吸
    property bool pressed: false                  // Pointer pressed state 按压状态
    property bool highlighted: false              // Hover/touch-active state 悬浮或触摸激活
    property bool enabledState: true              // Target enabled (false dims to ember) 目标启用状态(禁用时收敛为余辉)
    property bool reduceMotion: false             // Honour reduced-motion 尊重减少动态效果
    // A design language that forbids soft elevation reports zero here, so the halo
    // collapses instead of fighting that skin's own elevation paradigm.
    // 禁止柔和悬浮的设计语言在此报零, 光晕随之收敛, 而不是与该皮肤自身的悬浮范式冲突。
    property real spreadRatio: tokens.spreadRatio
    property real blurRatio: tokens.blurRatio

    // ==================== Readonly State 只读状态 ====================
    // Defensive target reads: a required property is non-null while the component
    // lives, but transient nulls still reach these bindings during teardown and
    // would spam "Cannot read property ... of null". A missing target simply
    // collapses the halo. 防御式读取 target: required 属性在组件存活期非空, 但销毁
    // 过程中绑定仍可能读到瞬时 null, 从而刷出 "Cannot read property ... of null"。
    // target 缺失时只需收敛光晕。
    readonly property bool _hasTarget: target !== null && target !== undefined
    readonly property real _shortEdge: _hasTarget
        ? Math.min(target.width, target.height) : 0
    readonly property real _spread: _shortEdge * spreadRatio
    readonly property real _blur: _shortEdge * blurRatio
    // A collapsed halo (zero spread) has nothing to draw; skip the whole node.
    // 收敛的光晕(零外扩)无可绘制内容, 跳过整个节点。
    readonly property bool _visible: active && _spread > 0
        && _hasTarget && target.visible
    // A hidden window must not keep animating: Qt still drives the animation clock
    // for invisible windows. 隐藏窗口不得继续动画: Qt 对不可见窗口仍驱动动画时钟。
    readonly property bool _windowShown: {
        var hostWindow = root.Window.window
        return hostWindow === null || hostWindow === undefined
            || hostWindow.visible === true
    }
    // A disabled surface keeps a static ember: pulsing it would imply the control is
    // still live, which reads as an affordance the user cannot actually use.
    // 禁用表面保留静态余辉: 让它呼吸会暗示控件仍可用, 读作一个用户无法真正使用的提示。
    readonly property bool animated: _visible && pulseEnabled && enabledState
        && !reduceMotion && _windowShown
    readonly property real _stateStrength: !enabledState
        ? tokens.disabledStrength
        : (pressed
           ? tokens.pressedStrength
           : (highlighted ? tokens.hoverStrength : 1.0))

    // ==================== Internal Props 内部属性 ====================
    property real _breath: 1.0

    // The halo overhangs the target, so it must not be clipped by it; anchor to the
    // target and let the shadow's negative margin carry the spread. A null target
    // cannot parent anything, so the halo stays unparented and invisible instead of
    // warning. 光晕向目标外侧溢出, 不能被目标裁剪; 因此锚定到目标, 由阴影的负边距
    // 承载外扩。null target 无法作为父级, 因此光晕保持无父且不可见而不是报警。
    parent: _hasTarget ? target : null
    anchors.fill: parent
    z: -1
    visible: _visible

    // ==================== Content 内容 ====================
    RectangularShadow {
        anchors.fill: parent
        anchors.margins: -root._spread
        radius: (root._hasTarget && root.target.radius !== undefined
                 ? root.target.radius : 0) + root._spread
        color: Qt.rgba(
            root.haloColor.r, root.haloColor.g, root.haloColor.b,
            root.tokens.restAlpha * root._breath * root._stateStrength)
        blur: root._blur
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
            from: root.tokens.pulseMin
            to: root.tokens.pulseMax
            duration: root.tokens.breatheDuration
            easing.type: Easing.InOutSine
        }
        NumberAnimation {
            target: root
            property: "_breath"
            from: root.tokens.pulseMax
            to: root.tokens.pulseMin
            duration: root.tokens.breatheDuration
            easing.type: Easing.InOutSine
        }
    }
}
