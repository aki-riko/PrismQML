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
    readonly property bool _shown: sheetControl._isOpen || sheetControl._isClosing
    readonly property real _lift: sheetControl.stackLift
    readonly property int _maxDepth: _skin.sheet.maxVisibleDepth

    anchors.fill: parent
    // Sheets past the visible depth fade out 超出可见深度的层淡出
    opacity: Math.max(0, Math.min(1, _maxDepth - _lift))

    // ==================== Content 内容 ====================
    // Soft elevation shadow 柔和投影
    RectangularShadow {
        anchors.fill: panel
        radius: surface._radius
        color: surface._skin.shadow.level28.color
        blur: surface._skin.shadow.level28.blur
        offset.x: 0
        offset.y: surface._skin.shadow.level28.offset
        visible: surface._skin.usesSoftElevation && !surface._skin.isNeumorphism
                 && surface._shown
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
            onDragStarted: surface.sheetControl._beginDrag()
            onDragMoved: (translationY) => surface.sheetControl._dragTo(translationY)
            onDragReleased: (translationY, velocityY) =>
                surface.sheetControl._endDrag(translationY, velocityY)
            onTapped: surface.sheetControl._toggleDetent()
        }

        Item {
            id: contentItem

            objectName: "contentItem"  // For Python findChild 供Python查找
            anchors.fill: parent
            anchors.margins: surface._skin.spacing.xl
            anchors.topMargin: grabber.visible ? grabber.height : surface._skin.spacing.xl
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
