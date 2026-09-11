# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML scene data strings used by scroll_bar_conventions_shared."""

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/ScrollBar" as Internal

Window {
    id: root
    objectName: "window"

    readonly property real verticalY: verticalFlick.contentY
    readonly property real verticalTarget: verticalHelper.targetPos
    readonly property real verticalMax: verticalHelper.maxScroll
    readonly property bool verticalOvershot: verticalHelper.isOvershot
    readonly property real horizontalX: horizontalFlick.contentX
    readonly property real horizontalMax: horizontalHelper.maxScroll
    readonly property real popupY: popupFlick.contentY
    readonly property real defaultX: defaultArea.contentX
    readonly property real defaultY: defaultArea.contentY
    readonly property real defaultContentWidth: defaultArea.contentWidth
    readonly property real defaultContentHeight: defaultArea.contentHeight
    readonly property real listY: listArea.contentY
    readonly property real listContentHeight: listArea.contentHeight
    readonly property int listCount: listArea.count
    readonly property real gridY: gridArea.contentY
    readonly property real gridOriginY: gridArea.gridView.originY
    readonly property real gridContentHeight: gridArea.contentHeight
    readonly property int gridCount: gridArea.count

    function scrollVertical() { verticalHelper.scrollTo(180) }
    function scrollVerticalToEnd() { verticalHelper.scrollToEnd() }
    function growVerticalContent() { verticalFlick.contentHeight = 720 }
    function overshootVertical() { verticalHelper.scrollBy(1000) }
    function syncVertical() {
        verticalFlick.contentY = 75
        verticalHelper.syncPosition()
    }
    function scrollHorizontal() { horizontalHelper.scrollTo(260) }
    function scrollHorizontalToEnd() { horizontalHelper.scrollToEnd() }
    function overshootHorizontal() { horizontalHelper.scrollBy(1000) }
    function growHorizontalContent() { horizontalFlick.contentWidth = 820 }
    function scrollPopup() { popupHelper.scrollTo(999) }
    function setVerticalHalf() {
        verticalFlick.contentY = 240
        verticalHelper.syncPosition()
    }
    function scrollDefault() {
        defaultArea.smoothScrollTo(160)
        defaultArea.smoothScrollToX(120)
    }
    // Move the scroll bounds while the axis is overshooting.
    function shrinkDefaultContent() { defaultContent.height = 390 }
    function restoreDefaultContent() { defaultContent.height = 420 }
    function scrollList() { listArea.scrollToIndex(10) }
    function scrollGrid() { gridArea.scrollToBottom() }

    width: 760
    height: 520
    visible: true

    Flickable {
        id: verticalFlick
        objectName: "verticalFlick"
        x: 20
        y: 20
        width: 180
        height: 120
        contentWidth: width
        contentHeight: 600
        clip: true
        interactive: false

        Rectangle {
            width: 180
            height: 600
        }
    }

    Internal.SmoothScrollHelper {
        id: verticalHelper
        objectName: "verticalHelper"
        target: verticalFlick
        duration: 100
    }

    Internal.ScrollBar {
        id: scrollBar
        objectName: "scrollBar"
        x: 210
        y: 20
        height: 120
        target: verticalFlick
        scrollHelper: verticalHelper
    }

    ScrollBarEntry {
        id: scrollBarEntry
        objectName: "scrollBarEntry"
        x: 230
        y: 20
        height: 120
        flickable: verticalFlick
    }

    Flickable {
        id: horizontalFlick
        objectName: "horizontalFlick"
        x: 20
        y: 170
        width: 180
        height: 100
        contentWidth: 700
        contentHeight: height
        clip: true
        interactive: false

        Rectangle {
            width: 700
            height: 100
        }
    }

    Internal.SmoothScrollHelper {
        id: horizontalHelper
        objectName: "horizontalHelper"
        target: horizontalFlick
        orientation: Qt.Horizontal
        duration: 100
    }

    Flickable {
        id: popupFlick
        objectName: "popupFlick"
        x: 20
        y: 300
        width: 180
        height: 100
        contentWidth: width
        contentHeight: 480
        clip: true
        interactive: false

        Rectangle {
            width: 180
            height: 480
        }

        Internal.PopupSmoothScroll {
            id: popupHelper
            objectName: "popupHelper"
            flickable: popupFlick
            duration: 100
        }
    }

    Component {
        id: listDelegate
        Rectangle {
            width: ListView.view ? ListView.view.width : 0
            height: 30
        }
    }

    Component {
        id: gridDelegate
        Rectangle {
            width: 60
            height: 40
        }
    }

    Internal.ScrollAreaDefault {
        id: defaultArea
        objectName: "defaultArea"
        x: 300
        y: 20
        width: 200
        height: 140
        padding: 10

        Rectangle {
            id: defaultContent
            width: 360
            height: 420
        }
    }

    Internal.ScrollAreaList {
        id: listArea
        objectName: "listArea"
        x: 300
        y: 190
        width: 180
        height: 120
        model: 20
        delegate: listDelegate
        itemHeight: 30
    }

    Internal.ScrollAreaGrid {
        id: gridArea
        objectName: "gridArea"
        x: 520
        y: 190
        width: 180
        height: 120
        model: 20
        delegate: gridDelegate
        cellWidth: 60
        cellHeight: 40
    }
}
"""
