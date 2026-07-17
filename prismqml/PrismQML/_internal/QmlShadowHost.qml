// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import ".."

// QmlShadowHost - Deferred QML shadow implementation 延迟加载的 QML 阴影实现
Item {
    id: root

    // ==================== Internal Props 内部属性 ====================
    readonly property var hostWindow: parent ? parent.hostWindow : null

    anchors.fill: parent
    Component.onCompleted: if (hostWindow && hostWindow.profileDetail) hostWindow.profileDetail("QmlShadowHost root completed")

    RectangularShadow {
        anchors.fill: shadowSource
        radius: shadowSource.radius
        color: Enums.shadow.level28.color
        blur: Enums.shadow.level28.blur
        offset.x: 0
        offset.y: Enums.shadow.level28.offset
        Component.onCompleted: if (root.hostWindow && root.hostWindow.profileDetail) root.hostWindow.profileDetail("QmlShadowHost RectangularShadow completed")
    }

    Rectangle {
        id: shadowSource
        anchors.centerIn: parent
        width: parent.width - (root.hostWindow ? root.hostWindow.shadowSize * 2 : 0)
        height: parent.height - (root.hostWindow ? root.hostWindow.shadowSize * 2 : 0)
        radius: root.hostWindow ? root.hostWindow.windowRadius : Enums.radius.large
        color: root.hostWindow ? root.hostWindow.windowColor : Enums.backgroundColor
        Component.onCompleted: if (root.hostWindow && root.hostWindow.profileDetail) root.hostWindow.profileDetail("QmlShadowHost shadowSource completed")
    }
}
