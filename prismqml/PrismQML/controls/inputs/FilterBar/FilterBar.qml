// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// FilterBar - Unified filter component 统一过滤器组件
// Usage 用法:
//   FilterBar { items: ["All", "Apps", "Documents"]; exclusive: true }  // 互斥
//   FilterBar { items: ["All", "Apps", "Documents"]; exclusive: false } // 多选
FilterBarCore {
    id: control

    // All props inherited from FilterBarCore 所有属性继承自基类
    // - items: []
    // - currentIndex: 0 (exclusive mode)
    // - exclusive: true
    // - selectedIndices: [0] (multi-select mode)
    // - enabled: true
    
    // Signals inherited 信号继承
    // - itemClicked(int index)
    // - selectionChanged(var indices)
    // - currentIndexChanged(int index)
}
