// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// PipsPager - Unified pips pager component 统一分页指示器组件
// Control via orientation property 通过orientation属性控制方向
// Orientation: Qt.Horizontal (1) / Qt.Vertical (2)
PipsPagerCore {
    id: control
    
    // ==================== Public Properties 公开属性 ====================
    property int orientation: Qt.Horizontal  // Qt.Horizontal (1) or Qt.Vertical (2)
    
    // ==================== Apply Orientation 应用方向 ====================
    vertical: orientation === Qt.Vertical
}
