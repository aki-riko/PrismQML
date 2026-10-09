// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Animation - Animation type enums 动画类型枚举
QtObject {
    readonly property int none: 0
    readonly property int opacity: 1
    readonly property int popup: 2
    readonly property int popdown: 3
    readonly property int slide_horizontal: 4
    readonly property int slide_vertical: 5
    readonly property int slide_fade: 6
    readonly property int card_horizontal: 7
    readonly property int card_vertical: 8
    readonly property int zoom: 9
}
