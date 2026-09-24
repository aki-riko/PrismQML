// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import QtQuick.Window
import "../../../.."

// DrawerOutsideWindow - Native outside drawer host 外侧抽屉原生承载窗口
// This HWND never carries a DWM shadow, so the seam side stays free of any shadow band.
// The drawer paints its own window shadow inside the outward padding instead.
// 该 HWND 始终不携带 DWM 阴影, 接缝侧因此不会出现阴影带; 抽屉改为在外侧留白内自绘窗口阴影。
Window {
    id: outsideDrawerWindow

    // ==================== Required Props 必需属性 ====================
    required property var drawerControl

    // ==================== Readonly State 只读状态 ====================
    readonly property var control: drawerControl
    readonly property alias panel: outsideDrawerPanel
    // Outward padding reserved for the self-drawn shadow 自绘阴影预留的外扩留白
    readonly property real spread: control._outsideShadowSpread
    readonly property real hostWidth: control._hostWindow
        ? control._hostWindow.width : control.drawerWidth
    readonly property real hostHeight: control._hostWindow
        ? control._hostWindow.height : control.drawerHeight
    // The panel keeps the full requested extent; only the HWND grows outwards
    // 面板保持请求的完整尺寸, 只有 HWND 朝外侧长大
    readonly property real panelWidth: control.isHorizontal
        ? control._outsideFullExtent : hostWidth
    readonly property real panelHeight: control.isHorizontal
        ? hostHeight : control._outsideFullExtent
    readonly property real panelOffsetX: control.isHorizontal
        ? (control.position === Enums.position.left ? spread : 0) : spread
    readonly property real panelOffsetY: control.isHorizontal
        ? spread : (control.position === Enums.position.top ? spread : 0)
    // Revealed extent along the host edge, plus the clip origin per position
    // 沿宿主边显露的范围, 以及各位置对应的裁剪原点
    readonly property real clipExtent: control.isHorizontal
        ? Math.min(control._outsideExtent, panelWidth)
        : Math.min(control._outsideExtent, panelHeight)
    readonly property real viewportX: control.isHorizontal
        && control.position !== Enums.position.left
        ? panelOffsetX : (control.isHorizontal ? width - clipExtent : panelOffsetX)
    readonly property real viewportY: control.isHorizontal
        || control.position !== Enums.position.top
        ? panelOffsetY : height - clipExtent

    objectName: "outsideDrawerWindow"
    x: 0
    y: 0
    width: control.isHorizontal ? panelWidth + spread : panelWidth + 2 * spread
    height: control.isHorizontal ? panelHeight + 2 * spread : panelHeight + spread
    visible: control._outsideVisible && control._hostWindow !== null
    opacity: control._outsidePrepared ? 1 : 0
    flags: Qt.Tool | Qt.FramelessWindowHint
    color: Enums.transparent
    transientParent: control._hostWindow

    onVisibleChanged: {
        if (visible) {
            control._applyOutsideNativeFrame()
            control._clearOutsideNativeShadow()
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

    // ==================== Content 内容 ====================
    // The HWND has no DWM shadow; this is the drawer's only outward shadow
    // 该 HWND 没有 DWM 阴影, 这里是抽屉唯一的外侧阴影
    RectangularShadow {
        id: outsideDrawerShadow

        anchors.fill: outsideDrawerViewport
        // Outward corners follow the panel; the seam side stays square, otherwise the
        // shadow arc would be painted inside the window and cut off by the host edge.
        // 外侧角跟随面板; 接缝侧保持直角, 否则阴影弧会画进窗口内并被宿主边硬切。
        radius: Enums.radius.none
        topLeftRadius: control.position === Enums.position.left
            || control.position === Enums.position.top
            ? outsideDrawerPanel.radius : Enums.radius.none
        topRightRadius: control.position === Enums.position.right
            || control.position === Enums.position.top
            ? outsideDrawerPanel.radius : Enums.radius.none
        bottomLeftRadius: control.position === Enums.position.left
            || control.position === Enums.position.bottom
            ? outsideDrawerPanel.radius : Enums.radius.none
        bottomRightRadius: control.position === Enums.position.right
            || control.position === Enums.position.bottom
            ? outsideDrawerPanel.radius : Enums.radius.none
        // Blur must stay inside the reserved padding or the shadow gets clipped
        // 模糊半径必须落在预留留白内, 否则阴影会被裁掉
        blur: Enums.shadow.windowOutside.blur
        color: Enums.shadow.windowOutside.color
        offset.x: 0
        offset.y: Enums.shadow.windowOutside.offset
        visible: control._outsideShadowActive && !Enums.isVintageTicket
    }

    // Clipped reveal viewport 裁剪显露视口
    Item {
        id: outsideDrawerViewport
        objectName: "outsideDrawerViewport"

        x: outsideDrawerWindow.viewportX
        y: outsideDrawerWindow.viewportY
        width: control.isHorizontal ? outsideDrawerWindow.clipExtent
                                    : outsideDrawerWindow.panelWidth
        height: control.isHorizontal ? outsideDrawerWindow.panelHeight
                                     : outsideDrawerWindow.clipExtent
        clip: true

        Rectangle {
            id: outsideDrawerPanel
            objectName: "outsideDrawerPanel"

            width: outsideDrawerWindow.panelWidth
            height: outsideDrawerWindow.panelHeight
            x: outsideDrawerWindow.panelOffsetX - outsideDrawerViewport.x
            y: outsideDrawerWindow.panelOffsetY - outsideDrawerViewport.y
            color: control._drawerBackground
            // All four panel corners stay rounded, matching the native window look
            // this padded HWND replaces. 面板四角保持圆角, 与它所替代的原生窗口外观一致。
            radius: control._effectiveRadius
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
