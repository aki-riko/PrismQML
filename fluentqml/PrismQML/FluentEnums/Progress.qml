// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Progress - Progress type enums 进度条类型枚举
QtObject {
    readonly property int type_bar: 0           // Bar 条形进度条
    readonly property int type_bar_filled: 1    // Filled bar with text 填充条形（带百分比）
    readonly property int type_ring: 2          // Ring 环形进度条
}
