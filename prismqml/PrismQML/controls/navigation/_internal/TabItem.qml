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
pragma ComponentBehavior: Bound
Item {
    id: tabItem

    // ==================== Required Props 必需属性 ====================
    required property Item host
    required property Item rowContainer
    required property var repeater
    required property int index
    required property var modelData

    // ==================== Readonly State 只读状态 ====================
    readonly property var _tabData: modelData && typeof modelData === "object" ? modelData : ({})
    readonly property string _title: {
        if (modelData && typeof modelData === "object") return String(modelData.title || "")
        return String(modelData || "")
    }
    readonly property string _subtitle: String(_tabData.subtitle || "")
    readonly property string _badgeText: _tabData.badgeText === undefined
        ? "" : String(_tabData.badgeText)
    readonly property int _badgeLevel: _tabData.badgeLevel === undefined
        ? Enums.statusLevel.info : Number(_tabData.badgeLevel)
    readonly property color _badgeColor: Enums.statusLevel.getColorByLevel(_badgeLevel)
    readonly property bool _hasDetails: !!host.detailsEnabled &&
        (_subtitle !== "" || _badgeText !== "")
    readonly property bool _tabEnabled: host.interactionEnabled && _tabData.enabled !== false
    readonly property bool _tabClosable: host.closable &&
        _tabData.closeEnabled !== false && host.tabCloseEnabled(index, modelData)
    readonly property real _contentImplicitWidth: _hasDetails
        ? detailContent.implicitWidth : compactContent.implicitWidth
    readonly property real _automaticWidth: Math.max(
        host.minimumTabWidth,
        _contentImplicitWidth + Enums.spacing.xl * 2 +
        (_tabClosable ? Enums.spacing.xxl : 0))

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
    width: {
        var value = host.tabWidth > 0 ? host.tabWidth : _automaticWidth
        if (host.maximumTabWidth > 0)
            value = Math.min(host.maximumTabWidth, value)
        return Math.max(host.minimumTabWidth, value)
    }
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
    opacity: _tabEnabled ? Enums.opacityLevel.visible : Enums.opacityLevel.disabled

    // ==================== Content 内容 ====================
    Rectangle {
        id: tabBg

        anchors.fill: parent
        anchors.margins: Enums.border.thin
        anchors.bottomMargin: Enums.border.thin
        radius: host._selectedTabRadius
        color: {
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
        id: compactContent

        visible: !tabItem._hasDetails
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: tabItem._tabClosable ? -Enums.spacing.l : 0
        spacing: Enums.spacing.s

        Icon {
            id: compactIcon

            icon: tabItem._tabData.icon ? tabItem._tabData.icon : ""
            iconSize: Enums.iconSize.m
            visible: icon !== ""
            anchors.verticalCenter: parent.verticalCenter
            opacity: tabItem.selected
                     ? Enums.opacityLevel.visible
                     : (Enums.isDark ? Enums.opacityLevel.strong
                                     : Enums.opacityLevel.secondary)
            color: Enums.foregroundColor

            Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
        }

        Label {
            id: compactText

            type: Enums.label.type_caption
            text: tabItem._title
            color: Enums.foregroundColor
            anchors.verticalCenter: parent.verticalCenter
            opacity: tabItem.selected
                     ? Enums.opacityLevel.visible
                     : (Enums.isDark ? Enums.opacityLevel.strong
                                     : Enums.opacityLevel.secondary)

            Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
        }
    }

    Column {
        id: detailContent
        objectName: "tabItemDetailContent"

        visible: tabItem._hasDetails
        width: host.tabWidth > 0
            ? Math.max(0, tabItem.width - Enums.spacing.xl * 2 -
                       (tabItem._tabClosable ? Enums.spacing.xxl : 0))
            : implicitWidth
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: tabItem._tabClosable ? -Enums.spacing.l : 0
        spacing: Enums.spacing.s

        Row {
            id: detailTitleRow

            width: detailContent.width
            spacing: Enums.spacing.xs

            Icon {
                id: detailIcon

                icon: tabItem._tabData.icon ? tabItem._tabData.icon : ""
                iconSize: Enums.iconSize.s
                visible: icon !== ""
                anchors.verticalCenter: parent.verticalCenter
                color: tabItem.selected ? Enums.accentColor : Enums.foregroundColor
            }

            Label {
                id: detailTitle

                width: Math.max(0, detailTitleRow.width -
                       (detailIcon.visible ? detailIcon.width : 0) -
                       (detailBadge.visible ? detailBadge.width : 0) -
                       (detailIcon.visible ? Enums.spacing.xs : 0) -
                       (detailBadge.visible ? Enums.spacing.xs : 0))
                type: Enums.label.type_caption
                text: tabItem._title
                color: Enums.foregroundColor
                font.bold: tabItem.selected
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
            }

            Label {
                id: detailBadge

                type: Enums.label.type_caption
                text: tabItem._badgeText
                visible: text !== ""
                customTextColor: tabItem._badgeColor
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        Label {
            id: detailSubtitle
            objectName: "tabItemDetailSubtitle"

            width: detailContent.width
            type: Enums.label.type_caption
            text: tabItem._subtitle
            visible: text !== ""
            color: Enums.textColor.secondary
            elide: Text.ElideRight
            wrapMode: Text.NoWrap
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
        visible: tabItem._tabClosable && (tabItem.selected || tabItem.hovered)
        enabled: tabItem._tabEnabled
        z: Enums.zIndex.header
        onClicked: host.tabClosed(index)
    }

    HoverHandler {
        id: tabHoverHandler

        enabled: tabItem._tabEnabled
        cursorShape: Qt.PointingHandCursor
    }

    TapHandler {
        id: tabTapHandler

        enabled: tabItem._tabEnabled
        onTapped: {
            host.currentIndex = index
            host.tabClicked(index)
        }
    }

    DragHandler {
        id: tabDragHandler

        property real _pressRowX: 0

        enabled: tabItem._tabEnabled && host.movable
        target: null
        xAxis.enabled: true
        yAxis.enabled: false
        dragThreshold: 6

        onActiveChanged: {
            if (active) {
                host._dragSourceIndex = index
                host._dragVisualIndex = index
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
            if (newVisual !== host._dragVisualIndex)
                host._dragVisualIndex = newVisual
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
