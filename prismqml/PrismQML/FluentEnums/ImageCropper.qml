// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// ImageCropper - Image cropper enums 图片裁剪枚举
QtObject {
    // Shape 形状
    readonly property int shape_rect: 0
    readonly property int shape_circle: 1
    readonly property int shape_square: 2
    
    // Display type 显示类型
    readonly property int type_dialog: 0   // Standalone window 独立窗口
    readonly property int type_overlay: 1  // Overlay on parent 遮罩覆盖
}
