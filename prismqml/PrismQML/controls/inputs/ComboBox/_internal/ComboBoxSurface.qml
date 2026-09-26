// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../../.."
import "../../../../effects"
import QtQuick.Effects
import QtQuick  // After library import: unprefixed native types stay unshadowed 置于库import后:去前缀后保原生类型不被库覆盖

// ComboBoxSurface - Control surface and skin elevation for ComboBox 下拉框控件表面与皮肤层级
// Owns the resting/open fill, the border and the three elevation layers, keeping every
// skin branch in one place; the content file only composes text, input, interaction and
// the candidate surface.
// 负责静止/展开底色、边框与三层阴影, 皮肤分支集中在一处; 内容文件只组合文本、输入、
// 交互与候选表面。
Item {
    id: surface

    // ==================== Required Props 必需属性 ====================
    required property var comboControl
    // Candidate surface close animation state 候选表面关闭动画状态
    required property bool popupClosing

    // ==================== Readonly State 只读状态 ====================
    // The surface is the only hover consumer left, so it owns the touch decision.
    // Touch has no hover preview: on touch the hover treatment follows the press.
    // 表面是仅存的悬浮消费者, 因此由它持有触摸决策; 触摸没有 hover 预览,
    // 触摸端 hover 视觉只在按压时生效。
    readonly property bool _touchActive: Touch.feedback(comboControl.hovered, comboControl.pressed)

    // ==================== Content 内容 ====================
    // Style helper 样式辅助
    ComboBoxStyleHelper {
        id: styleHelper
        control: surface.comboControl
    }

    // Shadow layer below background 背景下方阴影层
    // Fluent: 模糊阴影。Neobrutalism: 硬阴影(纯黑, 展开时转橙强调)。
    RectangularShadow {
        anchors.fill: background
        radius: background.radius
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset.x: 0
        offset.y: Enums.shadow.level2.offset
        visible: comboControl.style === 0 && Enums.usesSoftElevation && !Enums.isNeumorphism
    }

    NeumorphicShadow {
        target: background
        inset: true
        visible: comboControl.style === 0 && Enums.isNeumorphism
        z: background.z - 1
    }

    // Neobrutalism 硬阴影: 复用 NeoShadow 组件; 展开时 accent=true 转橙强调。
    NeoShadow {
        target: background
        visible: Enums.isNeobrutalism && comboControl.style === 0
        accent: comboControl.popupVisible
        z: background.z - 1
    }

    // Background 背景
    Rectangle {
        id: background
        anchors.fill: parent
        radius: comboControl.radius
        clip: false
        // No layer.effect mask here: it is a silent no-op in Qt 6.11 (see OpacityMask docs).
        // 这里不再使用 layer.effect 遮罩: 它在 Qt 6.11 下静默失效 (见 OpacityMask 文档)。

        // Fluent Design style Fluent Design样式
        // Unified with Button/LineEdit controlBg series 与Button/LineEdit统一使用controlBg系列
        color: {
            if (comboControl.style !== 0) return styleHelper.getBackgroundColor()
            if (!comboControl.enabled) return Enums.stateColor.controlBgDisabled
            // Expanded list keeps the resting fill and outranks hover/press, so the
            // open dropdown never overlays a colour on the control.
            // 展开下拉时锁定静止底色并优先于 hover/press, 展开态不给控件叠加任何颜色。
            if (comboControl.popupVisible) return Enums.stateColor.controlBg
            if (comboControl.pressed) return Enums.stateColor.controlBgPressed
            if (surface._touchActive) return Enums.stateColor.controlBgHover
            return Enums.stateColor.controlBg
        }

        // Fluent Design 边框:亮/暗主题各用低透明度描边,具体取值见 StateColor.pickerBorder
        border.width: comboControl.style !== 0
            ? 0
            : Enums.surfaceBorderWidth(Enums.border.thin)
        border.color: Enums.isNeobrutalism && comboControl.style === 0
            ? (!comboControl.enabled ? Enums.stateColor.comboBoxDisabledBorder
               : (comboControl.popupVisible ? Enums.neo.primary : Enums.neo.borderColor))
            : (Enums.isVintageTicket && comboControl.style === 0
               ? (!comboControl.enabled ? Enums.stateColor.borderLight
                  : (comboControl.popupVisible ? Enums.accentColor : Enums.borderColor))
            : styleHelper.getBorderColor()
            )

        // Color animation (not applied during close to avoid delay) 颜色动画
        HoverBehavior on color {
            active: surface._touchActive && !comboControl.pressed &&
                    !comboControl.popupVisible
            animationEnabled: !surface.popupClosing
            enterDuration: Enums.duration.fast
        }
    }
}
