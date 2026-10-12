// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../buttons"

// DesktopNotificationCloseButton - Desktop notification close affordance 桌面通知关闭按钮
// Owns the close-button visuals; the notification entry keeps state and signals.
// 持有关闭按钮的视觉实现; 通知入口只保留状态与信号。
Button {
    id: closeButton

    // ==================== Required Props 必需属性 ====================
    required property var host

    // ==================== Size 尺寸 ====================
    objectName: "closeBtn"
    anchors.right: parent.right
    anchors.rightMargin: Enums.spacing.l
    anchors.top: parent.top
    anchors.topMargin: Enums.spacing.l
    style: Enums.button.style_transparent
    icon: Enums.icon.dismiss
    width: Enums.spacing.xxl
    height: Enums.spacing.xxl
    radius: width / 2
    iconSize: Enums.iconSize.tiny
    iconColor: Enums.stateColor.scrollThumbHover
    focusOnPress: false
    visible: host.closable
    onClicked: host.hide()
}
