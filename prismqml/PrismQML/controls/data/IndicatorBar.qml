// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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
    property color inactiveColor: Enums.stateColor.pipNormal

    // Sizes 尺寸（短边为 thickness，长边随 active 在 inactiveLength/activeLength 间切换）
    property real thickness: 3
    property real inactiveLength: 14
    property real activeLength: 36

    // Animation duration 动画时长
    property int animationDuration: Enums.duration.medium

    // ==================== Internal Props 内部属性 ====================
    property color _animatedTop: _topColor
    property color _animatedBottom: _bottomColor

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isVertical: orientation === Enums.indicatorBar.orientation_vertical
    readonly property real _length: active ? activeLength : inactiveLength
    readonly property int _easingType: animationStyle === Enums.indicatorBar.animation_bounce
        ? Easing.OutBack
        : Easing.OutCubic
    readonly property color _indicatorActiveColor: activeColor
    readonly property color _indicatorInactiveColor: inactiveColor
    readonly property real _inactiveGradientAlpha: Enums.stateColor.indicatorInactiveGradientAlpha

    // Gradient end color: solid → same as top; gradient → darker accent / faded inactive
    // 渐变末端色：纯色模式与首端相同；渐变模式 → accent 深色 / inactive 更淡
    readonly property color _topColor: active ? _indicatorActiveColor : _indicatorInactiveColor
    readonly property color _bottomColor: {
        if (colorStyle === Enums.indicatorBar.style_solid) return _topColor
        if (active) return Qt.darker(_indicatorActiveColor, 1.4)
        return Qt.rgba(_indicatorInactiveColor.r, _indicatorInactiveColor.g, _indicatorInactiveColor.b, _indicatorInactiveColor.a * _inactiveGradientAlpha)
    }

    // ==================== Size 尺寸 ====================
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

    // Color animations 颜色动画
    // Two helper props with color behaviors feed the gradient stops 两个带颜色 Behavior 的辅助属性用于 GradientStop 输入
    Behavior on _animatedTop { ColorAnimation { duration: control.animationDuration } }
    Behavior on _animatedBottom { ColorAnimation { duration: control.animationDuration } }

    // Gradient (always used; solid uses matching endpoint colors) 渐变（始终使用；纯色模式两端同色）
    // Avoid visual jumps from dynamically switching gradient/color 避免动态切换 gradient/color 出现视觉跳变
    gradient: Gradient {
        orientation: control._isVertical ? Gradient.Vertical : Gradient.Horizontal
        GradientStop { position: 0.0; color: Enums.isVintageTicket ? control._animatedBottom : control._animatedTop }
        GradientStop { position: 1.0; color: control._animatedBottom }
    }
}
