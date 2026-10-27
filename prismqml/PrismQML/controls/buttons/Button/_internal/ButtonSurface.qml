// ButtonSurface - Button visual surface and color animation surface 按钮视觉表面与颜色动画表面
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../../effects"
import ".."

// ButtonSurface - Owns shadows, face, and animated surface colors 承载阴影、按钮面与动画颜色
Item {
    id: surface

    // ==================== Required Props 必需属性 ====================
    required property var buttonControl
    readonly property var _skin: buttonControl.effectiveSkinContext

    // ==================== Public Props 公开属性 ====================
    property alias background: background
    property alias border: background.border
    property alias bgColorAnimation: bgColorAnimation
    property alias borderColorAnimation: borderColorAnimation

    // ==================== Readonly State 只读状态 ====================
    readonly property real animatedPressShift:
        neoShadowLoader.item ? neoShadowLoader.item.animatedPressShift : 0
    readonly property var pressTransform:
        neoShadowLoader.item ? neoShadowLoader.item.pressTransform : null
    // Glow is an orthogonal layer: any style can request it. The layer is created on
    // demand rather than declared here, because every declaration costs resident
    // objects on *every* button: a Loader adds one, and an inline Component block
    // adds a QQmlComponent plus its attached object. That would change the measured
    // object counts of components that embed buttons (Toast, InfoBar, menus).
    // 泛光是正交图层: 任何样式都可请求它。该层按需创建而不是在此声明: 任何声明都会给
    // 每个按钮增加常驻对象(Loader 加一个, 内联 Component 块还会再加 QQmlComponent 及
    // 其 attached 对象), 从而改变内嵌按钮组件(Toast、InfoBar、菜单)的实测对象数。
    // A flat face has no fill for a bloom to sit behind, so it is excluded.
    // 无填充的扁平按钮没有可衬托光晕的面, 因此排除。
    readonly property bool _needsGlow: buttonControl._glowActive
                                       && !buttonControl.flat

    // ==================== Internal Props 内部属性 ====================
    property Item _glowLayer: null

    // ==================== Internal Methods 内部方法 ====================
    // Called by ButtonCore from its existing completion/state hooks: the surface
    // must not declare its own Component.onCompleted, because that attaches one
    // extra object to every button in the library.
    // 由 ButtonCore 通过它已有的完成/状态钩子调用: 表面不得声明自己的
    // Component.onCompleted, 否则会给库内每个按钮附加一个额外对象。
    function _syncGlowLayer() {
        if (_needsGlow) {
            if (_glowLayer !== null) return
            var component = Qt.createComponent("ButtonGlow.qml")
            if (!component || component.status !== Component.Ready) {
                // A failed component is a build-time defect; report it instead of
                // silently rendering a glow face without its halo.
                // 组件构建失败属于构建期缺陷; 显式报告而不是静默渲染一个没有光晕的泛光面。
                console.error("ButtonSurface: cannot create ButtonGlow:",
                              component ? component.errorString() : "no component")
                return
            }
            _glowLayer = component.createObject(surface, { "button": buttonControl })
            return
        }
        if (_glowLayer !== null) {
            _glowLayer.destroy()
            _glowLayer = null
        }
    }

    on_NeedsGlowChanged: _syncGlowLayer()

    // ==================== Size 尺寸 ====================
    anchors.fill: parent

    // ==================== Content 内容 ====================
    // Fluent shadow surface 流畅阴影表面
    // A glow face already carries its own bloom, so the Fluent soft shadow is
    // suppressed there; stacking both would read as a dirty double halo.
    // 泛光面自带光晕, 因此在泛光样式下抑制 Fluent 软阴影; 两者叠加会读作脏双影。
    RectangularShadow {
        anchors.fill: background
        radius: background.radius
        color: _skin.shadow.level2.color
        blur: _skin.shadow.level2.blur
        offset.x: 0
        offset.y: _skin.shadow.level2.offset
        visible: !surface.buttonControl.flat && _skin.usesSoftElevation
                 && !_skin.isNeumorphism && !_skin.isNeumorphism
                 && !surface.buttonControl._glowActive
    }

    // Neumorphic shadow surface 新拟态阴影表面
    NeumorphicShadow {
        target: background
        inset: surface.buttonControl.pressed
        pressed: surface.buttonControl.pressed
        visible: !surface.buttonControl.flat && _skin.isNeumorphism
        z: background.z - 1
    }

    // Lazy Neo shadow surface 懒加载 Neo 阴影表面
    Loader {
        id: neoShadowLoader
        active: _skin.isNeobrutalism && !surface.buttonControl.flat
        z: background.z - 1

        sourceComponent: ButtonNeoShadow {
            target: surface.background
            targetPressShift: surface.buttonControl._neoPressTargetShift
        }
    }

    // Background button face 按钮背景面
    Rectangle {
        id: background

        anchors.fill: parent
        radius: surface.buttonControl.radius
        color: surface.buttonControl._effectiveBgColor
        border.width: surface.buttonControl.flat ? 0 : _skin.surfaceBorderWidth(
            (surface.buttonControl._styleToggleChecked
             && surface.buttonControl.style === _skin.button.style_primary)
                ? _skin.border.normal : _skin.border.thin)
        border.color: surface.buttonControl._animatedBorderColor
        gradient: surface.buttonControl.style === _skin.button.style_gradient
                  && !_skin.isVintageTicket ? _skin._buttonGradientDef : null
        transform: surface.pressTransform
    }

    // Hover and press color animations 悬浮与按压颜色动画
    ColorAnimation {
        id: bgColorAnimation

        target: surface.buttonControl
        property: "_animatedBgColor"
        to: surface.buttonControl._targetBgColor
        duration: _skin.duration.medium
        easing.type: Easing.InOutCubic
    }

    ColorAnimation {
        id: borderColorAnimation

        target: surface.buttonControl
        property: "_animatedBorderColor"
        to: surface.buttonControl._targetBorderColor
        duration: _skin.duration.medium
    }
}
