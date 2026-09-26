// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import QtQuick.Window
import "../../../.."

// DrawerOutsideWindow - Native outside drawer host 外侧抽屉原生承载窗口
// No DWM shadow on this HWND, so the seam side stays free of any shadow band.
// 该 HWND 不带 DWM 阴影, 接缝侧因此不会出现阴影带。
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
    // The panel keeps its requested extent; the HWND grows by `spread` away from the host
    // edge and by `spread` on both sides across it, exactly like _follower_rect_for_extent.
    // 面板保持请求尺寸; HWND 朝外与跨接缝两侧各长 `spread`, 与 _follower_rect_for_extent 一致。
    readonly property real panelWidth: control.isHorizontal
        ? control._outsideFullExtent : hostWidth
    readonly property real panelHeight: control.isHorizontal
        ? hostHeight : control._outsideFullExtent
    readonly property real panelOffsetX: control.isHorizontal
        ? (control.position === Enums.position.left ? spread : 0) : spread
    readonly property real panelOffsetY: control.isHorizontal
        ? spread : (control.position === Enums.position.top ? spread : 0)
    readonly property real clipExtent: control.isHorizontal
        ? Math.min(control._outsideExtent, panelWidth)
        : Math.min(control._outsideExtent, panelHeight)
    readonly property real viewportX: control.isHorizontal
        ? (control.position === Enums.position.left ? width - clipExtent
                                                   : panelOffsetX)
        : panelOffsetX
    readonly property real viewportY: control.isHorizontal
        ? panelOffsetY
        : (control.position === Enums.position.top ? height - clipExtent
                                                   : panelOffsetY)

    objectName: "outsideDrawerWindow"
    x: 0
    y: 0
    // Native size, owned by _follower_rect_for_extent; the `width - clipExtent` reveal
    // below reads the same value.
    // 原生尺寸归 _follower_rect_for_extent 所有; 下面的 `width - clipExtent` 显露视口读同一个值。
    width: control.isHorizontal ? panelWidth + spread : panelWidth + 2 * spread
    height: control.isHorizontal ? panelHeight + 2 * spread : panelHeight + spread
    visible: control._outsideVisible && control._hostWindow !== null
    opacity: control._outsidePrepared ? 1 : 0
    flags: Qt.Tool | Qt.FramelessWindowHint
    color: Enums.transparent
    // Keep the outside drawer in the host's native owner group so modal dialogs stay above it.
    // 外层抽屉保持在宿主原生 owner 组内, 确保模态选择框位于抽屉之上。
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
    RectangularShadow {
        id: outsideDrawerShadow

        objectName: "outsideDrawerShadow"
        // The silhouette must stay equal to the panel. Measured on the real effect at
        // blur 40 / 0.50 black on white: a panel-sized silhouette reaches 21.6% darkening
        // at the panel edge — the DWM calibration target — and fades out within ~40px.
        // Growing the silhouette outwards by `blur` instead fills the first 40px beside the
        // panel with the full 49.8% and doubles the band width: the heavy edge users see.
        // 轮廓必须与面板等大。真实效果实测(blur 40, 0.50 黑, 白底): 轮廓等于面板时面板边缘
        // 暗化 21.6% —— 即 DWM 标定目标 —— 约 40px 内衰减完; 把轮廓朝外各扩 `blur` 会让紧邻
        // 面板的 40px 全是满浓度 49.8%, 并把像带宽度翻倍, 形成用户看到的浓重边缘。
        x: outsideDrawerWindow.panelOffsetX
        y: outsideDrawerWindow.panelOffsetY
        width: outsideDrawerWindow.panelWidth
        height: outsideDrawerWindow.panelHeight
        radius: outsideDrawerPanel.radius
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
