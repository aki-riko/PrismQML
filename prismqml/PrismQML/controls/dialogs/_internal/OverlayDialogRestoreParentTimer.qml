// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// OverlayDialogRestoreParentTimer - Finish dialog close state after animation
// OverlayDialogRestoreParentTimer - 动画结束后完成对话框关闭状态
Timer {
    id: restoreParentTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "overlayDialogRestoreParentTimer"
    interval: Enums.duration.medium + Enums.spacing.xl
    onTriggered: host._restoreParent()
}
