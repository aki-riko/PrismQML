// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Animation - Animation type enums 动画类型枚举
// Base transition family only; slide / slide_fade / card / pop / bounce run on the
// axis given by StackedWidget.animationOrientation (Qt.Horizontal / Qt.Vertical),
// and pop / bounce may pin their entry edge through StackedWidget.animationOrigin.
// 只描述基础过渡；slide / slide_fade / card / pop / bounce 的轴向由
// StackedWidget.animationOrientation 决定，pop / bounce 还可用 animationOrigin 钉住进入边。
QtObject {
    // ==================== Animation Types 动画类型 ====================
    readonly property int none: 0
    readonly property int opacity: 1
    // Short offset + fade in; pop lands smoothly, bounce lands elastically.
    // 短距位移 + 淡入；pop 平滑落位，bounce 回弹落位。
    readonly property int pop: 2
    readonly property int bounce: 3
    readonly property int slide: 4
    readonly property int slide_fade: 5
    readonly property int card: 6
    readonly property int zoom: 7
    // ==================== Entry Origins 进入边 ====================
    // Pop / bounce entry edge: origin_auto follows the switch direction, while a
    // pinned edge fixes the entry for both directions and overrides animationOrientation.
    // pop / bounce 进入边：origin_auto 跟随切换方向；钉住某个边时两个方向都固定该边，
    // 并忽略 animationOrientation。
    readonly property int origin_auto: 0
    readonly property int origin_top: Qt.TopEdge
    readonly property int origin_bottom: Qt.BottomEdge
    readonly property int origin_left: Qt.LeftEdge
    readonly property int origin_right: Qt.RightEdge
}
