// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import "../../../.."

// DrawerOutsideWindow - Native outside drawer host 外侧抽屉原生承载窗口
Window {
    id: outsideDrawerWindow

    // ==================== Required Props 必需属性 ====================
    required property var drawerControl

    // ==================== Readonly State 只读状态 ====================
    readonly property var control: drawerControl
    readonly property alias panel: outsideDrawerPanel

    objectName: "outsideDrawerWindow"
    x: 0
    y: 0
    width: control.drawerWidth
    height: control.drawerHeight
    visible: control._outsideVisible && control._hostWindow !== null
    opacity: control._outsidePrepared ? 1 : 0
    flags: Qt.Tool | Qt.FramelessWindowHint
    color: Enums.transparent
    transientParent: null

    onVisibleChanged: {
        if (visible) {
            control._applyOutsideNativeFrame()
            control._setOutsideNativeShadow(false)
            Qt.callLater(control._beginOutsideReveal)
        } else {
            control._unregisterOutsideWindow()
        }
    }
    onActiveChanged: {
        if (active && control._outsidePrepared) {
            control._scheduleOutsideHostSync()
        }
    }
    onClosing: (close) => control._resetDrawerState()
    Component.onDestruction: control._unregisterOutsideWindow()

    // Clipped reveal viewport 裁剪显露视口
    Item {
        id: outsideDrawerViewport
        objectName: "outsideDrawerViewport"

        x: control.position === Enums.position.left
            ? outsideDrawerWindow.width - width : 0
        y: control.position === Enums.position.top
            ? outsideDrawerWindow.height - height : 0
        width: control.isHorizontal
            ? Math.min(control._outsideExtent, outsideDrawerWindow.width)
            : outsideDrawerWindow.width
        height: control.isHorizontal
            ? outsideDrawerWindow.height
            : Math.min(control._outsideExtent, outsideDrawerWindow.height)
        clip: true

        Rectangle {
            id: outsideDrawerPanel
            objectName: "outsideDrawerPanel"

            width: outsideDrawerWindow.width
            height: outsideDrawerWindow.height
            x: -outsideDrawerViewport.x
            y: -outsideDrawerViewport.y
            color: control._drawerBackground
            radius: Enums.radius.none
            topLeftRadius: control.position === Enums.position.left
                || control.position === Enums.position.top
                ? control._effectiveRadius : Enums.radius.none
            topRightRadius: control.position === Enums.position.right
                || control.position === Enums.position.top
                ? control._effectiveRadius : Enums.radius.none
            bottomLeftRadius: control.position === Enums.position.left
                || control.position === Enums.position.bottom
                ? control._effectiveRadius : Enums.radius.none
            bottomRightRadius: control.position === Enums.position.right
                || control.position === Enums.position.bottom
                ? control._effectiveRadius : Enums.radius.none
            border.width: control._drawerBorderWidth
            border.color: control._drawerBorderColor

            TicketPaper {
                anchors.fill: parent
            }

            MouseArea {
                anchors.fill: parent
            }
        }
    }
}
