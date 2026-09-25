// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// NavigationIndicatorRecoveryTimer - Recover indicators after hidden-page activation
// NavigationIndicatorRecoveryTimer - 隐藏页面激活后恢复指示器
Timer {
    id: recoveryTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _needsRecovery:
        host && host._safeModel && host._safeModel.length > 0
        && !host._indicatorVisible

    // ==================== Size 尺寸 ====================
    interval: Enums.duration.slow
    repeat: true
    running: _needsRecovery

    // ==================== Content 内容 ====================
    onTriggered: host._initIndicatorPosition()
}
