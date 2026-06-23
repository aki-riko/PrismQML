// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Position - Position enums 位置枚举
QtObject {
    readonly property int left: 0
    readonly property int right: 1
    readonly property int top: 2
    readonly property int bottom: 3
    readonly property int center: 4
    readonly property int side: 5       // Side layout (icon left, text right) 侧边布局
    readonly property int top_left: 10
    readonly property int top_right: 11
    readonly property int bottom_left: 12
    readonly property int bottom_right: 13
}
