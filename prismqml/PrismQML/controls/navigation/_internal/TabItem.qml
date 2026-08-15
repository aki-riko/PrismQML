// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../buttons"
import "../../icons"
import "../../data"

// TabItem - Tab bar delegate with interaction and drag behavior
// TabItem - 带交互与拖拽行为的标签栏委托
Item {
    id: tabItem

    // ==================== Required Props 必需属性 ====================
    required property Item host
    required property Item rowContainer
    required property var repeater
    required property int index
    required property var modelData

    // ==================== Readonly State 只读状态 ====================
    property bool selected: index === host.currentIndex
    property bool hovered: tabHoverHandler.hovered
    property bool pressed: tabTapHandler.pressed
    readonly property bool isDragSource: host._dragging && index === host._dragSourceIndex
    readonly property int visualIndex: {
        if (!host._dragging) return index
        var src = host._dragSourceIndex
        var vis = host._dragVisualIndex
        if (index === src) return vis
        if (src < vis) {
            if (index > src && index <= vis) return index - 1
        } else if (src > vis) {
            if (index >= vis && index < src) return index + 1
        }
        return index
    }
    readonly property real visualOffsetX: {
        if (!host._dragging) return 0
        if (isDragSource) return host._dragSourceOffsetX
        return (visualIndex - index) * width
    }

    // ==================== Size 尺寸 ====================
    // Width adapts to content 宽度根据内容自适应
    width: Math.max(Enums.controlSize.segmentedMinWidth,
                    tabContent.implicitWidth + Enums.spacing.xl * 2
                    + (host.closable ? Enums.spacing.xxl : 0))
    height: host._tabHeight

    transform: Translate {
        x: tabItem.visualOffsetX
        Behavior on x {
            enabled: !tabItem.isDragSource
            NumberAnimation {
                duration: Enums.duration.fast
                easing.type: Easing.OutCubic
            }
        }
    }
    z: isDragSource ? Enums.zIndex.controlsAbove : Enums.zIndex.base
    opacity: 1.0

    // ==================== Content 内容 ====================
    // Background (non-selected state) 背景（非选中状态）
    Rectangle {
        id: tabBg

        anchors.fill: parent
        anchors.margins: Enums.border.thin
        anchors.bottomMargin: Enums.border.thin
        radius: host._selectedTabRadius
        color: {
            // Dragged tabs use a distinct surface to avoid selected-state ghosting.
            // 拖拽源使用独立表面，避免与选中态重叠产生视觉残影。
            if (tabItem.isDragSource) return Enums.stateColor.tabDragSource
            if (tabItem.selected) return Enums.transparent
            if (tabItem.pressed) return Enums.stateColor.tabPressed
            if (tabItem.hovered) return Enums.stateColor.hover
            return Enums.transparent
        }
        border.width: tabItem.isDragSource ? host._selectedTabBorderWidth : 0
        border.color: Enums.isDark ? Enums.stateColor.borderLight : Enums.stateColor.border

        HoverBehavior on color {
            active: tabItem.hovered && !tabItem.pressed
            enterDuration: Enums.duration.fast
        }
    }

    Row {
        id: tabContent

        anchors.centerIn: parent
        anchors.horizontalCenterOffset: host.closable ? -Enums.spacing.l : 0
        spacing: Enums.spacing.s

        Label {
            id: tabIcon

            type: Enums.label.type_body
            text: modelData && modelData.icon ? modelData.icon : ""
            visible: text !== ""
            anchors.verticalCenter: parent.verticalCenter
            opacity: tabItem.selected
                     ? Enums.opacityLevel.visible
                     : (Enums.isDark ? Enums.opacityLevel.strong
                                     : Enums.opacityLevel.secondary)
            color: Enums.foregroundColor

            Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
        }

        Label {
            id: tabText

            type: Enums.label.type_caption
            text: modelData ? (modelData.title || modelData) : ""
            color: Enums.foregroundColor
            anchors.verticalCenter: parent.verticalCenter
            opacity: tabItem.selected
                     ? Enums.opacityLevel.visible
                     : (Enums.isDark ? Enums.opacityLevel.strong
                                     : Enums.opacityLevel.secondary)

            Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
        }
    }

    CloseButton {
        id: closeBtn

        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.s
        anchors.verticalCenter: parent.verticalCenter
        size: Enums.iconSize.xxl
        iconSizeValue: Enums.iconSize.tiny
        normalIconColor: Enums.secondaryForeground
        visible: host.closable && (tabItem.selected || tabItem.hovered)
        z: Enums.zIndex.header
        onClicked: host.tabClosed(index)
    }

    HoverHandler {
        id: tabHoverHandler

        cursorShape: Qt.PointingHandCursor
    }

    TapHandler {
        id: tabTapHandler

        onTapped: {
            host.currentIndex = index
            host.tabClicked(index)
        }
    }

    DragHandler {
        id: tabDragHandler

        property real _pressRowX: 0

        enabled: host.movable
        target: null
        xAxis.enabled: true
        yAxis.enabled: false
        dragThreshold: 6

        onActiveChanged: {
            if (active) {
                host._dragSourceIndex = index
                host._dragVisualIndex = index
                // pressPosition is local while the tab transform is zero.
                // transform 为零时 pressPosition 可直接映射到标签行。
                var point = tabItem.mapToItem(
                    rowContainer, centroid.pressPosition.x, centroid.pressPosition.y)
                _pressRowX = point.x
                host._dragPointerRowX = point.x
                host._dragSourceOffsetX = 0
            } else if (host._dragSourceIndex >= 0) {
                var owner = host
                var from = host._dragSourceIndex
                var to = host._dragVisualIndex
                host._dragSourceIndex = -1
                host._dragVisualIndex = -1
                host._dragSourceOffsetX = 0
                if (from !== to && from >= 0 && to >= 0) {
                    owner.tabsReordered(from, to)
                    owner.currentIndex = to
                }
            }
        }

        onActiveTranslationChanged: {
            if (!active) return
            host._dragSourceOffsetX = activeTranslation.x
            var pointerRowX = _pressRowX + activeTranslation.x
            host._dragPointerRowX = pointerRowX
            var widthValue = tabItem.width
            if (widthValue <= 0) return
            var sourceCenterRowX = index * widthValue + activeTranslation.x + widthValue / 2
            var newVisual = Math.max(
                0, Math.min((host._safeTabs || []).length - 1,
                            Math.floor(sourceCenterRowX / widthValue)))
            if (newVisual !== host._dragVisualIndex) {
                host._dragVisualIndex = newVisual
            }
        }
    }

    Separator {
        id: separator

        type: Enums.separator.vertical
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        lineLength: Enums.iconSize.small
        visible: {
            if (host._dragging) return false
            if (index >= (host._safeTabs || []).length - 1) return false
            if (tabItem.selected) return false
            if (index + 1 === host.currentIndex) return false
            if (tabItem.hovered) return false
            var nextItem = repeater.itemAt(index + 1)
            if (nextItem && nextItem.hovered) return false
            return true
        }
    }
}
