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
    property list<Component> pageComponents
    property var pageSources: []

    Item { id: _hiddenStack; visible: false }
    default property alias pages: _hiddenStack.data

    // ==================== Content Layout ====================
    content: Item {
        anchors.fill: parent

        Timer {
            id: startupTimer
            interval: 50
            running: true
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
            asynchronous: true

            onLoaded: {
                window.profileTime("WindowsBar mainLoader.onLoaded start")
                window.navigationView = item.navAlias
                window.stackedWidget = item.stackAlias
                window.profileTime("WindowsBar bind navigation/stack")

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
