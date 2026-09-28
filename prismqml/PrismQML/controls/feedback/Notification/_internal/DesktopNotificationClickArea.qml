// DesktopNotificationClickArea - Card click capture 通知卡片点击捕获
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

Item {
    id: clickArea

    required property var host

    anchors.fill: parent
    MouseArea {
        anchors.fill: parent
        z: Enums.zIndex.background
        onClicked: clickArea.host.clicked()
    }
}
