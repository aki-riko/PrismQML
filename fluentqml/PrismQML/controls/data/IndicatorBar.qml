// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."

// IndicatorBar - Animated indicator/accent bar 动画指示器/重音条
// Use as visual anchor in lists, navigation, selection states 用于列表/导航/选中态的视觉锚点
//
// Three independent style enums 三个独立样式枚举:
//   1. colorStyle: solid / gradient 纯色 / 渐变
//   2. animationStyle: normal (OutCubic) / bounce (OutBack) 普通缓动 / 弹性回弹
//   3. orientation: vertical / horizontal 竖向 / 横向
//
// Drives stretch-on-active animation: short inactive → long active 由 active 切换实现"短→长"的拉伸动画
// 通用展示: 列表项 hover/选中、导航项指示器、卡片侧栏锚点
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Style enums 样式枚举
    property int orientation: Enums.indicatorBar.orientation_vertical
    property int colorStyle: Enums.indicatorBar.style_solid
    property int animationStyle: Enums.indicatorBar.animation_normal

    // Active state (hover / selected) 激活状态
    property bool active: false

    // Colors 颜色
    property color activeColor: Enums.accentColor
    property color inactiveColor: Enums.isDark ? Qt.rgba(1, 1, 1, 0.16) : Qt.rgba(0, 0, 0, 0.16)

    // Sizes 尺寸（短边为 thickness，长边随 active 在 inactiveLength/activeLength 间切换）
    property real thickness: 3
    property real inactiveLength: 14
    property real activeLength: 36

    // Animation duration 动画时长
    property int animationDuration: 250

    // ==================== Internal 内部 ====================
    readonly property bool _isVertical: orientation === Enums.indicatorBar.orientation_vertical
    readonly property real _length: active ? activeLength : inactiveLength
    readonly property int _easingType: animationStyle === Enums.indicatorBar.animation_bounce
        ? Easing.OutBack
        : Easing.OutCubic

    // Gradient end color: solid → same as top; gradient → darker accent / faded inactive
    // 渐变末端色：纯色模式与首端相同；渐变模式 → accent 深色 / inactive 更淡
    readonly property color _topColor: active ? activeColor : inactiveColor
    readonly property color _bottomColor: {
        if (colorStyle === Enums.indicatorBar.style_solid) return _topColor
        if (active) return Qt.darker(activeColor, 1.4)
        return Qt.rgba(inactiveColor.r, inactiveColor.g, inactiveColor.b, inactiveColor.a * 0.25)
    }

    // ==================== Geometry 几何 ====================
    width: _isVertical ? thickness : _length
    height: _isVertical ? _length : thickness
    radius: thickness / 2
    color: Enums.transparent
    antialiasing: true

    Behavior on width {
        enabled: !control._isVertical
        NumberAnimation { duration: control.animationDuration; easing.type: control._easingType }
    }
    Behavior on height {
        enabled: control._isVertical
        NumberAnimation { duration: control.animationDuration; easing.type: control._easingType }
    }

    // ==================== Color Animations 颜色动画 ====================
    // Two helper props with Behavior on color, fed into GradientStops below
    // 两个带 Behavior 的辅助属性，用作 GradientStop 的 color 输入
    property color _animatedTop: _topColor
    property color _animatedBottom: _bottomColor
    Behavior on _animatedTop { ColorAnimation { duration: control.animationDuration } }
    Behavior on _animatedBottom { ColorAnimation { duration: control.animationDuration } }

    // ==================== Gradient (always used; solid = same color top/bottom) ====================
    // 始终用 gradient（纯色模式两端同色），避免动态切换 gradient/color 出现视觉跳变
    gradient: Gradient {
        orientation: control._isVertical ? Gradient.Vertical : Gradient.Horizontal
        GradientStop { position: 0.0; color: control._animatedTop }
        GradientStop { position: 1.0; color: control._animatedBottom }
    }
}
