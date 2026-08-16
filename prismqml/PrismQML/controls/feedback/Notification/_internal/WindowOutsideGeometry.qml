// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// WindowOutsideGeometry - Host-relative native placement helper
// WindowOutsideGeometry - 宿主相对原生外侧定位辅助
QtObject {
    id: helper

    // ==================== Required Props 必需属性 ====================
    required property var hostWindow
    required property int position
    required property real targetWidth
    required property real targetHeight
    required property real stackOffset

    // ==================== Public Props 公开属性 ====================
    property real gap: Enums.notification.layout.windowOutsideGap

    // ==================== Public Methods 公开方法 ====================
    function calculate() {
        if (!hostWindow || typeof WindowHelper === "undefined" || !WindowHelper)
            return null
        return WindowHelper.windowAttachmentGeometry(
            hostWindow,
            position,
            targetWidth,
            targetHeight,
            gap,
            stackOffset
        )
    }
}
