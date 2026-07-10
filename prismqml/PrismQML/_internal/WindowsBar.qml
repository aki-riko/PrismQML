// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// WindowsBar - Top navigation window bar
// Extends NavigationWindowCore with NavigationBar (icon+text vertical)
NavigationWindowCore {
    id: window

    windowTitle: ""
    titleBarHeight: Enums.spacing.xxxl * 2
    titleBarLeftMargin: Enums.spacing.xxl

    // ==================== Compact Navigation Props ====================
    property int contentTopMargin: Enums.spacing.none

    // ==================== Lazy Loading Aliases ====================
    property var pageSources: []

    Component.onCompleted: window.profileDetail(
        "WindowsBar root completed nav=" + navigationItems.length +
        " bottom=" + bottomNavigationItems.length +
        " hidden=" + _hiddenStack.data.length
    )

    Item {
        id: _hiddenStack
        visible: false
        Component.onCompleted: window.profileDetail("WindowsBar hiddenStack completed count=" + data.length)
    }
    default property alias pages: _hiddenStack.data

    // ==================== Content Layout ====================
    content: Item {
        anchors.fill: parent
        Component.onCompleted: window.profileDetail("WindowsBar content shell completed")

        Timer {
            id: startupTimer
            interval: 0
            running: true
            Component.onCompleted: window.profileDetail("WindowsBar startupTimer completed running=" + running + " interval=" + interval)
            onRunningChanged: window.profileDetail("WindowsBar startupTimer running=" + running)
            onTriggered: {
                window.profileTime("WindowsBar startupTimer triggered")
                mainLoader.setSource(Qt.resolvedUrl("WindowsBarContent.qml"), {
                    "hostWindow": window,
                    "contentTopMargin": window.contentTopMargin
                })
                mainLoader.active = true
                window.profileTime("WindowsBar mainLoader.active=true")
            }
        }

        Loader {
            id: mainLoader
            anchors.fill: parent
            active: false
            asynchronous: false
            Component.onCompleted: window.profileDetail("WindowsBar mainLoader completed active=" + active + " status=" + status)
            onActiveChanged: window.profileDetail("WindowsBar mainLoader active=" + active + " status=" + status)
            onStatusChanged: window.profileDetail("WindowsBar mainLoader status=" + status + " active=" + active + " source=" + source)

            onLoaded: {
                window.profileTime("WindowsBar mainLoader.onLoaded start")
                window.profileDetail("WindowsBar mainLoader loaded item=" + item)
                window.navigationView = item.navAlias
                window.stackedWidget = item.stackAlias
                window.profileTime("WindowsBar bind navigation/stack navReady=" + (window.navigationView !== null))

                if (_hiddenStack.data.length > 0) {
                    window.profileTime("WindowsBar move hidden pages start count=" + _hiddenStack.data.length)
                    let container = window.stackedWidget.containerItem
                    let items = []
                    for (let i = 0; i < _hiddenStack.data.length; i++) {
                        items.push(_hiddenStack.data[i])
                    }
                    for (let i = 0; i < items.length; i++) {
                        let child = items[i]
                        child.parent = container
                        child.width = Qt.binding(function() { return container.width })
                        child.height = Qt.binding(function() { return container.height })
                        child.x = 0
                        child.y = 0
                        child.scale = 1
                        child.visible = (i === window.stackedWidget.currentIndex)
                        child.opacity = (i === window.stackedWidget.currentIndex ? 1 : 0)
                    }
                    window.profileTime("WindowsBar move hidden pages done")
                }

                window.profileTime("WindowsBar dismissSplashWhenReady start")
                window._dismissSplashWhenReady(window.stackedWidget)
                window.profileTime("WindowsBar dismissSplashWhenReady done")
            }
        }
    }
}
