// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"

// SurfaceUnavailable - Graceful fallback for an unavailable surface 表面不可用时的优雅回退
// Rendered instead of crashing when an optional Qt module cannot be loaded.
// 可选 Qt 模块无法加载时渲染此回退，而不是崩溃。
Item {
    id: control

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Readonly State 只读状态 ====================
    readonly property string message: host.errorString !== ""
        ? host.errorString
        : host.unavailableMessage

    // ==================== Size 尺寸 ====================
    anchors.fill: parent

    // ==================== Content 内容 ====================
    Rectangle {
        anchors.fill: parent
        color: Enums.surfaceColor
        radius: Enums.radius.small
    }

    Column {
        anchors.centerIn: parent
        width: Math.max(0, control.width - Enums.spacing.xl)
        spacing: Enums.spacing.s

        Icon {
            anchors.horizontalCenter: parent.horizontalCenter
            icon: Enums.icon.alert
            iconSize: Enums.iconSize.xxl
            color: Enums.secondaryForeground
        }

        Text {
            width: parent.width
            visible: control.message !== ""
            text: control.message
            color: Enums.secondaryForeground
            font.family: Enums.fontFamily
            font.pixelSize: Enums.typography.caption
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
    }
}
