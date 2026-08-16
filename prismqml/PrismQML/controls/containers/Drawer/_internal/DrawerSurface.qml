// DrawerSurface - Inside drawer visual layer 内侧抽屉视觉层
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../../effects"

// DrawerSurface - Owns panel, shadows and movable content 承载面板、阴影与可移动内容
Item {
    id: surface

    // ==================== Required Props 必需属性 ====================
    required property var drawerControl

    // ==================== Public Props 公开属性 ====================
    default property alias content: contentItem.data
    readonly property alias panel: drawer

    anchors.fill: parent

    // ==================== Content 内容 ====================
    // Drawer shadow 抽屉阴影
    // Shadow for drawer 抽屉阴影
    RectangularShadow {
        anchors.fill: drawer
        radius: surface.drawerControl._effectiveRadius
        color: Enums.shadow.level28.color
        blur: Enums.shadow.level28.blur
        offset.x: 0
        offset.y: Enums.shadow.level28.offset
        visible: Enums.usesSoftElevation && !Enums.isNeumorphism
                 && (surface.drawerControl._isOpen
                     || surface.drawerControl._isClosing)
    }

    NeumorphicShadow {
        target: drawer
        visible: Enums.isNeumorphism
                 && (surface.drawerControl._isOpen
                     || surface.drawerControl._isClosing)
        z: drawer.z - 1
    }

    // Drawer panel 抽屉面板
    Rectangle {
        id: drawer

        readonly property real effectiveWidth:
            surface.drawerControl.width > 0
            ? surface.drawerControl.width
            : (surface.drawerControl.parent
               ? surface.drawerControl.parent.width : 0)
        readonly property real effectiveHeight:
            surface.drawerControl.height > 0
            ? surface.drawerControl.height
            : (surface.drawerControl.parent
               ? surface.drawerControl.parent.height : 0)

        color: surface.drawerControl._drawerBackground
        radius: surface.drawerControl._effectiveRadius
        // Drawer boundary for non-Fluent skins 非 Fluent 皮肤抽屉边界
        border.width: surface.drawerControl._drawerBorderWidth
        border.color: surface.drawerControl._drawerBorderColor

        // Use parent size directly when control size is 0 (Python setParentItem timing issue)
        // 当 control 尺寸为 0 时直接使用 parent 尺寸（Python setParentItem 时序问题）
        width: surface.drawerControl.isHorizontal
            ? surface.drawerControl.drawerWidth : effectiveWidth
        height: surface.drawerControl.isHorizontal
            ? effectiveHeight : surface.drawerControl.drawerHeight

        TicketPaper {
            anchors.fill: parent
        }

        // Block clicks from reaching the overlay mask 阻止点击穿透到遮罩层
        MouseArea {
            anchors.fill: parent
            // Consume all clicks so they don't propagate to the mask 消费点击防止穿透
        }

        // Use states to manage position 使用states管理位置
        states: [
            State {
                name: "open"
                when: surface.drawerControl._isOpen
                PropertyChanges {
                    target: drawer
                    x: surface.drawerControl.position === Enums.position.left ? 0
                       : (surface.drawerControl.position === Enums.position.right
                          ? drawer.effectiveWidth - drawer.width : 0)
                    y: surface.drawerControl.position === Enums.position.top ? 0
                       : (surface.drawerControl.position === Enums.position.bottom
                          ? drawer.effectiveHeight - drawer.height : 0)
                }
            },
            State {
                name: "closed"
                when: !surface.drawerControl._isOpen
                PropertyChanges {
                    target: drawer
                    x: surface.drawerControl.position === Enums.position.left
                       ? -drawer.width
                       : (surface.drawerControl.position === Enums.position.right
                          ? drawer.effectiveWidth : 0)
                    y: surface.drawerControl.position === Enums.position.top
                       ? -drawer.height
                       : (surface.drawerControl.position === Enums.position.bottom
                          ? drawer.effectiveHeight : 0)
                }
            }
        ]

        transitions: Transition {
            enabled: surface.drawerControl._insideAnimationReady
            NumberAnimation {
                properties: "x,y"
                duration: surface.drawerControl.animationDuration
                easing.type: Easing.OutCubic
            }
        }
    }

    // Shared content host moves between inside and outside panels
    // 共享内容宿主在内侧与外侧面板间移动
    Item {
        id: contentItem

        objectName: "contentItem"  // For Python findChild 供Python查找
        parent: surface.drawerControl._isOutside
            ? surface.drawerControl._outsideDrawerPanel : drawer
        anchors.fill: parent
        anchors.margins: Enums.spacing.xl

        // Clear input focus when clicking empty content area 点击内容空白处清除输入焦点
        MouseArea {
            anchors.fill: parent
            z: Enums.zIndex.background
            onClicked: contentItem.forceActiveFocus()
        }
    }
}
