// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Orient - Layout orientation enums 布局方向枚举
// Required parameter for Layout component 布局组件的必选参数
// Must be specified explicitly, no default value 必须显式指定，无默认值
QtObject {
    id: root
    
    // ==================== Orientation Types 方向类型 ====================
    readonly property int flow: 0        // Flow layout (uses Flow sub-enum) 流式布局（使用Flow子枚举）
    readonly property int vertical: 1    // Vertical layout (VBoxLayout) 垂直布局
    readonly property int horizontal: 2  // Horizontal layout (HBoxLayout) 水平布局
    readonly property int grid: 3        // Grid layout 网格布局
}
