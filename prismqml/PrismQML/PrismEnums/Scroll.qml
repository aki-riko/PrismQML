// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Scroll - Scroll area type enums 滚动区域类型枚举
QtObject {
    readonly property int type_default: 0
    readonly property int type_list: 1
    readonly property int type_grid: 2
    readonly property real boundary_epsilon: 0.000001
    // Smallest foreign contentX/Y move treated as a revoked overshoot.
    // 视为超出被撤销的最小外部 contentX/Y 位移。
    readonly property real revocation_epsilon: 0.5
    // Idle gap that ends one continuous relative-scroll burst.
    // 结束一次连续相对滚动输入串的空闲间隙。
    readonly property int input_burst_gap: 120
}
