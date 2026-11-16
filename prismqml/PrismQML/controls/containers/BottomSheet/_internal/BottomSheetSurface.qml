// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../../effects"

// BottomSheetSurface - Bottom sheet panel, shadows and content host 底部弹层面板、阴影与内容宿主
Item {
    id: surface

    // ==================== Required Props 必需属性 ====================
    required property var sheetControl

    // ==================== Public Props 公开属性 ====================
    default property alias content: contentItem.data
    readonly property alias panel: panel

    // ==================== Internal Props 内部属性 ====================
    readonly property var _skin: sheetControl._skin
    readonly property real _radius: _skin.surfaceRadius(_skin.radius.xlarge)
    // Follows the reveal, not the base restore timer: a slide-out can outlast it.
    // 跟随显露进度而不是基类恢复计时器：滑出可能比计时器更久。
    readonly property bool _shown: sheetControl._isOpen || sheetControl._isClosing
                                   || sheetControl.revealProgress > 0
    readonly property real _lift: sheetControl.stackLift
    readonly property int _maxDepth: _skin.sheet.maxVisibleDepth
    readonly property bool _softShadow: _skin.usesSoftElevation && !_skin.isNeumorphism
                                        && _shown

    anchors.fill: parent

    // ==================== Content 内容 ====================
    // Scrim tied to the reveal, so the page dims exactly as far as the sheet has risen
    // and brightens back as it leaves, dragging included. Only the bottom sheet draws
    // it, so stacking never darkens the page further. It ignores input: the base
    // class's transparent scrim still blocks and dismisses.
    // 遮罩与显露进度绑定：面板升起多少页面就暗多少，离开时同步变亮，拖拽中也一样。
    // 只有最底层绘制，叠层不会让页面更暗。它不接收输入，拦截与点按关闭仍由基类的
    // 透明遮罩负责。
    Rectangle {
        objectName: "bottomSheetScrim"
        anchors.fill: parent
        color: surface._skin.stateColor.dialogOverlay
        opacity: surface.sheetControl.revealProgress
        visible: surface.sheetControl.stackIndex <= 0 && opacity > 0
    }

    // Shadows, panel and dim layer; deep sheets fade out without touching the scrim.
    // 阴影、面板与压暗层；深层淡出时不影响遮罩。
    Item {
        id: sheetLayer

        anchors.fill: parent
        // Sheets past the visible depth fade out 超出可见深度的层淡出
        opacity: Math.max(0, Math.min(1, surface._maxDepth - surface._lift))

        // The sheet rises from the host bottom, so its shadows cast upward: a downward
        // offset would land below the window edge where nothing shows. A tight contact
        // shadow defines the seam over the sheet below; a wide ambient one gives lift.
        // 弹层从宿主底部升起，阴影须向上投：向下偏移会落到窗口底边以外，看不见。
        // 贴边的接触阴影勾出压在下层上的接缝，宽幅的环境阴影提供抬升感。
        RectangularShadow {
            objectName: "bottomSheetAmbientShadow"
            anchors.fill: panel
            radius: surface._radius
            color: surface._skin.shadow.level28.color
            blur: surface._skin.shadow.level28.blur
            offset.x: 0
            offset.y: -surface._skin.shadow.level28.offset
            scale: panel.scale
            transformOrigin: Item.Top
            visible: surface._softShadow
        }

        RectangularShadow {
            objectName: "bottomSheetContactShadow"
            anchors.fill: panel
            radius: surface._radius
            color: surface._skin.shadow.level4.color
            blur: surface._skin.shadow.level4.blur
            offset.x: 0
            offset.y: -surface._skin.shadow.level4.offset
            scale: panel.scale
            transformOrigin: Item.Top
            visible: surface._softShadow
        }

        NeumorphicShadow {
            target: panel
            visible: surface._skin.isNeumorphism && surface._shown
            z: panel.z - 1
        }

        // Sheet panel: only the top corners are rounded 弹层面板：仅顶部两角圆角
        Rectangle {
            id: panel

            objectName: "bottomSheetPanel"
            x: (surface.width - width) / 2
            y: surface.sheetControl.panelTop
            width: surface.sheetControl.sheetWidth
            height: surface.sheetControl.sheetHeight
            // Covered sheets shrink about their top edge 被覆盖层以顶边为基准缩小
            transformOrigin: Item.Top
            scale: 1 - surface._skin.sheet.stackScaleStep
                   * Math.min(surface._lift, surface._maxDepth)
            color: surface._skin.cardColor
            topLeftRadius: surface._radius
            topRightRadius: surface._radius
            // Panel boundary for outlined skins 描边皮肤面板边界
            border.width: surface._skin.hasOutlinedSurfaces
                          ? surface._skin.surfaceBorderWidth(surface._skin.border.thin) : 0
            border.color: surface._skin.hasOutlinedSurfaces
                          ? surface._skin.stateColor.border : surface._skin.transparent

            TicketPaper {
                anchors.fill: parent
            }

            // Consume clicks so they never reach the scrim 消费点击，防止穿透到遮罩
            MouseArea {
                anchors.fill: parent
            }

            BottomSheetGrabber {
                id: grabber

                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                visible: surface.sheetControl.showGrabber
                sheetControl: surface.sheetControl
                onDragStarted: surface.sheetControl._drag.begin()
                onDragMoved: (translationY) => surface.sheetControl._drag.moveTo(translationY)
                onDragReleased: (translationY, velocityY) =>
                    surface.sheetControl._drag.release(translationY, velocityY)
                onTapped: surface.sheetControl._toggleDetent()
            }

            Item {
                id: contentItem

                objectName: "contentItem"  // For Python findChild 供Python查找
                anchors.fill: parent
                anchors.margins: surface._skin.spacing.xl
                anchors.topMargin: grabber.visible ? grabber.height : surface._skin.spacing.xl
            }

            // Edge highlight: shadows barely show against a dark page, so a hairline keeps
            // the panel's silhouette. Its bottom edge is pushed below the panel, off the host.
            // 边缘高光：深色页面上阴影几乎不可见，用细描边保住面板轮廓。底边推到面板下方，
            // 落在宿主之外。
            Rectangle {
                objectName: "bottomSheetEdge"
                anchors.fill: parent
                anchors.bottomMargin: -surface._radius
                color: surface._skin.transparent
                topLeftRadius: surface._radius
                topRightRadius: surface._radius
                border.width: surface._skin.border.thin
                border.color: surface._skin.stateColor.border
                visible: surface._softShadow && !surface._skin.hasOutlinedSurfaces
            }

            // Dim layer over covered sheets 被覆盖层的压暗层
            Rectangle {
                objectName: "bottomSheetDim"
                anchors.fill: parent
                color: surface._skin.stateColor.dialogOverlay
                topLeftRadius: surface._radius
                topRightRadius: surface._radius
                opacity: Math.min(1, surface._lift) * surface._skin.sheet.stackDimOpacity
                visible: opacity > 0
            }
        }
    }
}
