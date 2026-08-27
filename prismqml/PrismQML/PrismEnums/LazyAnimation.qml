// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// LazyAnimation - Lazy-loading transition type enums 懒加载过渡类型枚举
QtObject {
    // Values remain stable for persisted ConfigManager settings 值保持稳定以兼容持久化配置
    readonly property int none: 10
    readonly property int lazy_circle: 7
    readonly property int custom: 8
    readonly property int cpu: 9
}
