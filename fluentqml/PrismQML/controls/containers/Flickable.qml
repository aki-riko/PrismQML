// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."

// Flickable - Basic scrollable container 基础可滚动容器
// For Python-side ScrollBar demo Python侧ScrollBar演示用
Flickable {
    id: control
    
    // Default size 默认尺寸
    implicitWidth: 200
    implicitHeight: 150
    
    // Clip content 裁剪内容
    clip: true
    
    // Bounce effect 回弹效果
    boundsBehavior: Flickable.StopAtBounds
    
}
