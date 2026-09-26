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
    // The panel keeps the full requested extent; only the HWND grows outwards. Padding is
    // symmetric across the seam, so the panel's seam-facing edge sits `spread` inside this
    // HWND and lines up exactly with the host edge — and that inset is what gives the
    // self-drawn shadow its room, since a flush panel clips its own blur on every side.
    // 面板保持请求的完整尺寸, 只有 HWND 朝外长大。留白跨接缝对称, 面板朝接缝那一侧因此也在
    // 本 HWND 内缩进 `spread`, 正好与宿主边缘对齐; 正是这段内缩给了自绘阴影空间。
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
    width: panelWidth + 2 * spread
    height: panelHeight + 2 * spread
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

        // The silhouette is the panel grown outwards by `blur`, not the panel itself.
        // `RectangularShadow` spreads its blur into AND out of the given rectangle, so a
        // silhouette equal to the panel hides the outer half of every band and the dark
        // band starts short of the panel edge — the reported clipped shadow. Growing it
        // by exactly `blur` centres each band on the panel edge, so the blur fades across
        // the seam the same way it fades on the outward side.
        // 轮廓是面板朝外各扩 `blur`, 而非面板本身。该效果的模糊会同时向轮廓内外铺开, 轮廓等于
        // 面板会让每条边的外半边像带不可见, 暗带起点落在面板边缘内侧 —— 即所报告的阴影被裁剪。
        // 正好外扩 `blur` 可让暗带中心线落在面板边缘, 模糊跨接缝的渐变因此与朝外一侧一致。
        x: outsideDrawerWindow.panelOffsetX - blur
        y: outsideDrawerWindow.panelOffsetY - blur
        width: outsideDrawerWindow.panelWidth + 2 * blur
        height: outsideDrawerWindow.panelHeight + 2 * blur
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
