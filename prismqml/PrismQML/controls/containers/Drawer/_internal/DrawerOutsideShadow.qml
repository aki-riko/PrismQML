// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import QtQuick.Window
import "../../../.."

// DrawerOutsideShadow - Outside drawer window shadow with a seam-side ramp 外侧抽屉窗口阴影(含接缝侧渐变)
// The seam-side `rampWidth` is cut into one-physical-pixel strips whose opacity climbs
// linearly; every boundary sits on a whole physical pixel, so the strips tile without
// gaps or overlaps (unsnapped adjacent clips leave hairlines at fractional DPR).
// 接缝侧 `rampWidth` 切成 1 物理像素宽的条带, 不透明度线性爬升; 所有边界落在整物理像素上,
// 条带无缝无重叠地拼接 (未对齐的相邻裁剪在小数缩放下会留发丝缝)。
Item {
    id: outsideShadow

    // ==================== Required Props 必需属性 ====================
    required property var hostWindow

    // ==================== Readonly State 只读状态 ====================
    readonly property var control: hostWindow.control
    readonly property var token: Enums.shadow.windowOutside
    readonly property real dpr: Screen.devicePixelRatio > 0 ? Screen.devicePixelRatio : 1
    readonly property int rampStrips: Math.max(1, Math.round(token.rampWidth * dpr))
    readonly property real axisExtent: control.isHorizontal ? hostWindow.width : hostWindow.height
    // Left/top drawers meet the host at the HWND's far edge 左/上抽屉在 HWND 远端与宿主相接
    readonly property bool seamAtFarEdge: control.position === Enums.position.left
        || control.position === Enums.position.top

    // ==================== Size 尺寸 ====================
    anchors.fill: parent
    visible: control._outsideShadowActive && !Enums.isVintageTicket

    // ==================== Content 内容 ====================
    Repeater {
        model: outsideShadow.rampStrips

        ShadowSlice {
            required property int index

            near: index / outsideShadow.dpr
            far: (index + 1) / outsideShadow.dpr
            opacity: (index + 1) / (outsideShadow.rampStrips + 1)
        }
    }

    ShadowSlice {
        near: outsideShadow.rampStrips / outsideShadow.dpr
        far: outsideShadow.axisExtent
        shadowName: "outsideDrawerShadow"
    }

    // Distances measured from the seam along the drawer axis 沿抽屉轴、自接缝起量的距离
    component ShadowSlice: Item {
        id: slice

        property real near
        property real far
        property string shadowName: ""

        x: !outsideShadow.control.isHorizontal ? 0
            : (outsideShadow.seamAtFarEdge ? outsideShadow.axisExtent - far : near)
        y: outsideShadow.control.isHorizontal ? 0
            : (outsideShadow.seamAtFarEdge ? outsideShadow.axisExtent - far : near)
        width: outsideShadow.control.isHorizontal ? far - near : outsideShadow.hostWindow.width
        height: outsideShadow.control.isHorizontal ? outsideShadow.hostWindow.height : far - near
        clip: true

        RectangularShadow {
            objectName: slice.shadowName
            // The silhouette stays equal to the panel; growing it by `blur` doubles the band
            // and saturates the panel edge. 轮廓必须与面板等大; 朝外扩 `blur` 会让像带翻倍并
            // 使面板边缘饱和。
            x: outsideShadow.hostWindow.panelOffsetX - slice.x
            y: outsideShadow.hostWindow.panelOffsetY - slice.y
            width: outsideShadow.hostWindow.panelWidth
            height: outsideShadow.hostWindow.panelHeight
            radius: outsideShadow.hostWindow.panel.radius
            blur: outsideShadow.token.blur
            color: outsideShadow.token.color
            offset.x: 0
            offset.y: outsideShadow.token.offset
        }
    }
}
