// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ButtonDropdownPrewarmTimer - Defer dropdown geometry preparation
// ButtonDropdownPrewarmTimer - 延迟执行下拉菜单几何预热
Timer {
    id: geometryPrewarmTimer

    // ==================== Required Props 必需属性 ====================
    required property var dropdownControl

    // ==================== Size 尺寸 ====================
    interval: 0

    // ==================== Content 内容 ====================
    onTriggered: dropdownControl._prewarmMenuGeometry()
}
