// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Animation - Animation type enums 动画类型枚举
// Base transition family only; the axis of slide / slide_fade / card comes from
// StackedWidget.animationOrientation (Qt.Horizontal / Qt.Vertical).
// 只描述基础过渡；slide / slide_fade / card 的轴向由 StackedWidget.animationOrientation 决定。
QtObject {
    readonly property int none: 0
    readonly property int opacity: 1
    readonly property int popup: 2
    readonly property int popdown: 3
    readonly property int slide: 4
    readonly property int slide_fade: 5
    readonly property int card: 6
    readonly property int zoom: 7
}
