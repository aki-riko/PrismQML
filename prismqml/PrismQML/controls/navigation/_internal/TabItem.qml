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
    // Touch has no hover preview: on touch the hover treatment follows the press
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
    readonly property bool _touchActive: Touch.feedback(hovered, pressed)
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
    readonly property bool vertical: host.vertical
    // Main axis is X for horizontal tabs and Y for vertical ones; the drag step,
    // the visual offset and the cell size all follow it.
    // 主轴: 横向为 X, 纵向为 Y; 拖拽步长、位移与单元尺寸都跟随它。
    readonly property real _mainSize: vertical ? height : width
    readonly property real _mainVisualOffset: {
        if (!host._dragging) return 0
        if (isDragSource) return host._dragSourceOffsetX
        return (visualIndex - index) * _mainSize
    }
    readonly property real visualOffsetX: vertical ? 0 : _mainVisualOffset
    readonly property real visualOffsetY: vertical ? _mainVisualOffset : 0
    // Space a full-width vertical row may use before the close affordance
    // 整宽纵向行在关闭入口之前可用的宽度
    readonly property real _verticalContentWidth: Math.max(
        0,
        width - Enums.spacing.m * 2 -
            (_tabClosable ? Enums.iconSize.xxl : 0))

    // ==================== Size 尺寸 ====================
    // Content-driven main-axis extent, shared by both orientations
    // 由内容决定的主轴长度, 两个方向共用
    readonly property real _mainExtent: {
        var value = host.tabWidth > 0 ? host.tabWidth : _automaticWidth
        if (host.maximumTabWidth > 0)
            value = Math.min(host.maximumTabWidth, value)
        return Math.max(host.minimumTabWidth, value)
    }
    width: vertical ? host._verticalCellWidth : _mainExtent
    height: vertical ? _mainExtent : host._tabHeight

    transform: Translate {
        x: tabItem.visualOffsetX
        y: tabItem.visualOffsetY
        Behavior on x {
            enabled: !tabItem.isDragSource
            NumberAnimation {
                duration: Enums.duration.fast
                easing.type: Easing.OutCubic
            }
        }
        Behavior on y {
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
            if (tabItem._touchActive) return Enums.stateColor.hover
            return Enums.transparent
        }
        border.width: tabItem.isDragSource ? host._selectedTabBorderWidth : 0
        border.color: Enums.isDark ? Enums.stateColor.borderLight : Enums.stateColor.border

        HoverBehavior on color {
            active: tabItem._touchActive && !tabItem.pressed
            enterDuration: Enums.duration.fast
        }
    }

    Row {
        id: compactContent

        visible: !tabItem._hasDetails
        // Vertical cells are full-width rows, so the content starts at the leading
        // edge instead of being centred. 纵向单元是整行宽, 内容改为从起始边排布。
        anchors.centerIn: tabItem.vertical ? undefined : parent
        anchors.left: tabItem.vertical ? parent.left : undefined
        anchors.leftMargin: tabItem.vertical ? Enums.spacing.m : 0
        anchors.verticalCenter: tabItem.vertical ? parent.verticalCenter : undefined
        anchors.horizontalCenterOffset: (tabItem.vertical || !tabItem._tabClosable)
            ? 0 : -Enums.spacing.l
        width: tabItem.vertical ? tabItem._verticalContentWidth : implicitWidth
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
            // Row-layout cells must elide instead of overflowing the strip
            // 整行布局的单元需要省略号, 避免溢出标签条
            width: tabItem.vertical
                ? Math.max(0, compactContent.width -
                           (compactIcon.visible
                                ? compactIcon.width + Enums.spacing.s : 0))
                : compactText.implicitWidth
            elide: tabItem.vertical ? Text.ElideRight : Text.ElideNone
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
        width: tabItem.vertical
            ? Math.max(0, tabItem.width - Enums.spacing.m * 2 -
                       (tabItem._tabClosable ? Enums.iconSize.xxl : 0))
            : (host.tabWidth > 0
                ? Math.max(0, tabItem.width - Enums.spacing.xl * 2 -
                           (tabItem._tabClosable ? Enums.spacing.xxl : 0))
                : implicitWidth)
        anchors.centerIn: tabItem.vertical ? undefined : parent
        anchors.left: tabItem.vertical ? parent.left : undefined
        anchors.leftMargin: tabItem.vertical ? Enums.spacing.m : 0
        anchors.verticalCenter: tabItem.vertical ? parent.verticalCenter : undefined
        anchors.horizontalCenterOffset: (tabItem.vertical || !tabItem._tabClosable)
            ? 0 : -Enums.spacing.l
        spacing: Enums.spacing.xxs

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
        // Hover only reveals the close affordance on desktop; with no hover preview on
        // touch it must stay reachable, so closable tabs keep it visible there
        // 桌面端仅由 hover 揭示关闭入口; 触摸端没有 hover 预览, 可关闭标签需常显该入口
        visible: tabItem._tabClosable && Touch.reveal(tabItem.selected || tabItem.hovered)
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
        acceptedButtons: Qt.LeftButton
        onTapped: {
            host.currentIndex = index
            host.tabClicked(index)
        }
    }

    TapHandler {
        enabled: tabItem._tabEnabled && host.contextMenuEnabled
        acceptedButtons: Qt.RightButton
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onTapped: function(eventPoint) {
            var hostPosition = tabItem.mapToItem(
                host, eventPoint.position.x, eventPoint.position.y)
            host.tabContextMenuRequested(
                index, Qt.point(hostPosition.x, hostPosition.y))
        }
    }

    DragHandler {
        id: tabDragHandler

        property real _pressRowMain: 0

        enabled: tabItem._tabEnabled && host.movable
        target: null
        // Only the main axis drags, so reordering stays 1-D in both orientations
        // 只有主轴参与拖拽, 因此两个方向的重排都是一维的
        xAxis.enabled: !tabItem.vertical
        yAxis.enabled: tabItem.vertical
        dragThreshold: 6

        onActiveChanged: {
            if (active) {
                host._dragSourceIndex = index
                host._dragVisualIndex = index
                var point = tabItem.mapToItem(
                    rowContainer, centroid.pressPosition.x, centroid.pressPosition.y)
                _pressRowMain = tabItem.vertical ? point.y : point.x
                host._dragPointerRowX = _pressRowMain
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
            var translation = tabItem.vertical
                ? activeTranslation.y : activeTranslation.x
            host._dragSourceOffsetX = translation
            var pointerRowMain = _pressRowMain + translation
            host._dragPointerRowX = pointerRowMain
            var extent = tabItem._mainSize
            if (extent <= 0) return
            var sourceCenterRowMain = index * extent + translation + extent / 2
            var newVisual = Math.max(
                0, Math.min((host._safeTabs || []).length - 1,
                            Math.floor(sourceCenterRowMain / extent)))
            if (newVisual !== host._dragVisualIndex)
                host._dragVisualIndex = newVisual
        }
    }

    Separator {
        id: separator

        type: tabItem.vertical
            ? Enums.separator.horizontal : Enums.separator.vertical
        anchors.right: tabItem.vertical ? undefined : parent.right
        anchors.verticalCenter: tabItem.vertical ? undefined : parent.verticalCenter
        anchors.bottom: tabItem.vertical ? parent.bottom : undefined
        anchors.horizontalCenter: tabItem.vertical ? parent.horizontalCenter : undefined
        lineLength: Enums.iconSize.small
        visible: {
            if (host._dragging) return false
            if (index >= (host._safeTabs || []).length - 1) return false
            if (tabItem.selected) return false
            if (index + 1 === host.currentIndex) return false
            if (tabItem._touchActive) return false
            var nextItem = repeater.itemAt(index + 1)
            if (nextItem && nextItem._touchActive) return false
            return true
        }
    }
}
