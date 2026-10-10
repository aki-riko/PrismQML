// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// SplitViewContent - SplitView visual layer 分栏视图视觉层
// Owns the content viewport, the pane surface, the light dismiss scrim, the resize
// hit area and the pane toggle. 承载内容视口、面板表面、轻触关闭遮罩、拖拽命中区与面板开关。
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Public Props 公开属性 ====================
    default property alias content: contentHost.data
    property alias paneContent: paneHost.data

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _resizable: host.paneResizeEnabled && host.isPaneOpen
    readonly property real _toggleLead:
        Math.max(host.contentOffset, host.paneExtent)

    // ==================== Internal Props 内部属性 ====================
    property real _pressX: 0
    property real _pressLength: 0

    // ==================== Internal Methods 内部方法 ====================
    // Start a divider drag 开始拖拽分隔条
    function _beginResize(mouse) {
        _pressX = resizeArea.mapToItem(content, mouse.x, 0).x
        _pressLength = host.openPaneLength
    }

    // Apply a divider drag in both directions 双向应用拖拽位移
    function _updateResize(mouse) {
        if (!resizeArea.pressed) return
        var currentX = resizeArea.mapToItem(content, mouse.x, 0).x
        var grow = host.isPaneRight ? _pressX - currentX : currentX - _pressX
        host.setPaneLength(_pressLength + grow)
    }

    // ==================== Content 内容 ====================
    // Main content viewport 主内容视口
    Item {
        id: contentHost
        objectName: "splitViewContentHost"
        x: content.host.isPaneRight ? 0 : content.host.contentOffset
        width: Math.max(0, content.width - content.host.contentOffset)
        height: content.height
        clip: true

        Behavior on x {
            NumberAnimation {
                duration: Enums.duration.fast
                easing.type: Easing.OutCubic
            }
        }
        Behavior on width {
            NumberAnimation {
                duration: Enums.duration.fast
                easing.type: Easing.OutCubic
            }
        }
    }

    // Light dismiss scrim 轻触关闭遮罩
    Rectangle {
        id: dismissScrim
        objectName: "splitViewDismissScrim"
        anchors.fill: parent
        visible: content.host.isLightDismissActive
        color: Enums.stateColor.dialogOverlay
        z: Enums.zIndex.base

        MouseArea {
            objectName: "splitViewDismissArea"
            anchors.fill: parent
            onClicked: content.host._handleLightDismiss()
        }
    }

    // Pane surface 面板表面
    Rectangle {
        id: paneSurface
        objectName: "splitViewPane"
        visible: content.host.isPaneVisible && width > 0
        color: Enums.cardColor
        width: Math.max(0, content.host.paneExtent)
        height: content.height
        x: content.host.isPaneRight ? content.width - width : 0
        z: Enums.zIndex.controls
        clip: true

        Behavior on width {
            NumberAnimation {
                duration: Enums.duration.fast
                easing.type: Easing.OutCubic
            }
        }
        Behavior on x {
            NumberAnimation {
                duration: Enums.duration.fast
                easing.type: Easing.OutCubic
            }
        }

        // Pane content 面板内容
        Item {
            id: paneHost
            objectName: "splitViewPaneHost"
            anchors.fill: parent
        }

        // Inner edge divider 内侧分隔线
        Rectangle {
            id: paneEdge
            objectName: "splitViewPaneEdge"
            width: Enums.border.thin
            height: parent.height
            x: content.host.isPaneRight ? 0 : parent.width - width
            color: Enums.dividerColor
        }
    }

    // Divider drag hit area 分隔条拖拽命中区
    MouseArea {
        id: resizeArea
        objectName: "splitViewResizeArea"
        enabled: content._resizable
        visible: enabled
        width: Math.max(Enums.controlSize.scrollBarWidth, Enums.border.thick)
        height: content.height
        x: content.host.isPaneRight
            ? Math.max(0, content.width - content.host.paneExtent - width / 2)
            : Math.min(content.width - width,
                       content.host.paneExtent - width / 2)
        z: Enums.zIndex.controlsAbove
        hoverEnabled: true
        cursorShape: Qt.SplitHCursor
        onPressed: (mouse) => content._beginResize(mouse)
        onPositionChanged: (mouse) => content._updateResize(mouse)
    }

    // Pane toggle 面板开关
    Rectangle {
        id: paneToggle

        readonly property real restingX: content.host.isPaneRight
            ? Math.max(0, content.width - content._toggleLead
                       - width - Enums.spacing.xs)
            : content._toggleLead + Enums.spacing.xs
        // Touch has no hover preview: on touch the hover treatment follows the press
        // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
        readonly property bool _touchActive:
            Touch.feedback(toggleArea.containsMouse, toggleArea.pressed)

        objectName: "splitViewPaneToggle"
        visible: content.host.paneToggleEnabled
        width: Enums.controlSize.commandBarButtonSize
        height: width
        radius: Enums.radius.small
        x: restingX
        y: 0
        z: Enums.zIndex.controlsAbove
        color: toggleArea.pressed
            ? Enums.pressedColor
            : (paneToggle._touchActive ? Enums.hoverColor : Enums.transparent)
        HoverBehavior on color {
            active: paneToggle._touchActive && !toggleArea.pressed
            enterDuration: Enums.duration.fast
        }

        Icon {
            objectName: "splitViewPaneToggleIcon"
            anchors.centerIn: parent
            icon: Enums.icon.navigation
            size: Enums.iconSize.xl
            color: Enums.foregroundColor
        }

        MouseArea {
            id: toggleArea
            objectName: "splitViewPaneToggleArea"
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: content.host.togglePane()
        }
    }
}
