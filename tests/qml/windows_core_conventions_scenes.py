# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML scene data strings used by windows_core_conventions_shared."""

SCENE_SOURCE = b"""
import QtQuick
import PrismQML

WindowsCore {
    id: root
    objectName: "window"
    property bool initialLeftLayout: false
    property bool customClose: false
    property bool noneClose: false
    property int customCollapseCount: 0
    property int customStopCount: 0
    property int nativeCloseAcceptedCount: 0
    readonly property int topLayout: Enums.windowType.title_bar_top
    readonly property int leftLayout: Enums.windowType.title_bar_left
    readonly property int noneAnimationType: Enums.lazyAnimation.none
    readonly property int noShadow: Enums.windowShadow.mode_none
    readonly property int qmlShadow: Enums.windowShadow.mode_qml
    readonly property int nativeShadow: Enums.windowShadow.mode_native
    readonly property int navPanelMinWidth: Enums.window.navPanelMinWidth
    readonly property int dividerWidth: Enums.border.thin
    readonly property int resizeDelay: Enums.window.resizeHandlesDelayMs
    readonly property int resizeEdge: Enums.window.resizeEdge
    readonly property int resizeCorner: Enums.window.resizeCorner

    width: 720
    height: 520
    visible: true
    shadowMode: Enums.windowShadow.mode_none
    windowTitle: "WindowsCore Contract"
    windowIcon: Qt.resolvedUrl("../../examples/resources/image/avatar/avatar.png")
    titleBarPosition: initialLeftLayout ? leftLayout : topLayout
    closeAnimationType: noneClose
        ? Enums.lazyAnimation.none
        : (customClose ? Enums.lazyAnimation.custom : Enums.lazyAnimation.lazy_circle)
    closeAnimation: customClose ? customCloseComponent : null

    onNativeCloseAccepted: nativeCloseAcceptedCount += 1

    Item {
        objectName: "contentProbe"
        width: 20
        height: 20
    }

    leftPanelContent: [
        Item {
            objectName: "leftProbe"
            width: 16
            height: 16
        }
    ]

    Component {
        id: customCloseComponent

        Item {
            property bool active: false
            property bool running: false
            property bool collapsing: false
            property bool collapsed: false
            property real progress: 0

            signal collapseStarted()
            signal collapseFinished()
            signal expandStarted()
            signal expandFinished()

            function collapse(sourceItem) {
                root.customCollapseCount += 1
                active = true
                running = true
                collapsing = true
                collapseStarted()
                progress = 1
                sourceItem.visible = false
                collapsed = true
                running = false
                active = false
                collapseFinished()
                return true
            }

            function expand(sourceItem) {
                sourceItem.visible = true
                collapsed = false
                expandStarted()
                expandFinished()
                return true
            }

            function stop() {
                root.customStopCount += 1
                active = false
                running = false
                collapsed = false
            }
        }
    }
}
"""
