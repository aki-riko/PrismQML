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
    property bool _startupHostActive: true
    readonly property bool _compactNav:
        typeof PlatformInfo !== "undefined" && PlatformInfo.isCompact

    function _pageIndexOf(item) {
        if (!item || item.objectName === undefined) return -1
        var name = String(item.objectName)
        if (name.indexOf("page_") !== 0) return -1
        var index = parseInt(name.substring(5))
        return isNaN(index) ? -1 : index
    }

    function _addPageItems(target, source) {
        if (!source) return
        for (var i = 0; i < source.length; i++) {
            var child = source[i]
            if (_pageIndexOf(child) >= 0 && target.indexOf(child) < 0) {
                target.push(child)
            }
        }
    }

    function _collectPageItems() {
        var items = []
        _addPageItems(items, _hiddenStack.data)
        _addPageItems(items, startupPageContainer.data)
        items.sort(function(a, b) { return _pageIndexOf(a) - _pageIndexOf(b) })
        return items
    }

    function _findPageItem(index) {
        var items = _collectPageItems()
        for (var i = 0; i < items.length; i++) {
            if (_pageIndexOf(items[i]) === index) return items[i]
        }
        return null
    }

    function _bindPageToContainer(child, container, visible) {
        child.parent = container
        child.width = Qt.binding(function() { return container.width })
        child.height = Qt.binding(function() { return container.height })
        child.x = 0
        child.y = 0
        child.scale = 1
        child.visible = visible
        child.opacity = visible ? 1 : 0
    }

    function _mountStartupPage(index) {
        if (!_startupHostActive) return false
        var child = _findPageItem(index)
        if (!child) return false
        _bindPageToContainer(child, startupPageContainer, true)
        profileTime("WindowsBar startup host mounted page_" + index)
        return true
    }

    function notifyStartupPageReady(index) {
        if (mainLoader.status === Loader.Ready) return
        var pageIndex = index === undefined ? currentIndex : Number(index)
        if (pageIndex !== currentIndex) return
        if (!_mountStartupPage(pageIndex)) return
        profileTime("WindowsBar startup page ready index=" + pageIndex)
        _dismissSplashWhenReady(null)
    }

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

        ContentFrame {
            id: startupContentFrame
            anchors.left: parent.left
            anchors.leftMargin: window._compactNav ? 0 : Enums.controlSize.navBarWidth
            anchors.top: parent.top
            anchors.topMargin: window.contentTopMargin
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            visible: window._startupHostActive
            backgroundColor: window.contentBgColor
            cornerRadius: window.contentCornerRadius
            Component.onCompleted: {
                window.profileDetail("WindowsBar startup ContentFrame completed")
                window._mountStartupPage(window.currentIndex)
            }

            Item {
                id: startupPageContainer
                objectName: "startupPageContainer"
                anchors.fill: parent
                Component.onCompleted: window.profileDetail("WindowsBar startup page container completed")
            }
        }

        Timer {
            id: startupTimer
            interval: 50
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
            asynchronous: true
            Component.onCompleted: window.profileDetail("WindowsBar mainLoader completed active=" + active + " status=" + status)
            onActiveChanged: window.profileDetail("WindowsBar mainLoader active=" + active + " status=" + status)
            onStatusChanged: window.profileDetail("WindowsBar mainLoader status=" + status + " active=" + active + " source=" + source)

            onLoaded: {
                window.profileTime("WindowsBar mainLoader.onLoaded start")
                window.profileDetail("WindowsBar mainLoader loaded item=" + item)
                window.navigationView = item.navAlias
                window.stackedWidget = item.stackAlias
                window.profileTime("WindowsBar bind navigation/stack")

                let items = window._collectPageItems()
                if (items.length > 0) {
                    window.profileTime("WindowsBar move hidden pages start count=" + items.length)
                    let container = window.stackedWidget.containerItem
                    for (let i = 0; i < items.length; i++) {
                        let child = items[i]
                        window._bindPageToContainer(child, container, i === window.stackedWidget.currentIndex)
                    }
                    window._startupHostActive = false
                    window.profileTime("WindowsBar move hidden pages done")
                }

                window.profileTime("WindowsBar dismissSplashWhenReady start")
                window._dismissSplashWhenReady(window.stackedWidget)
                window.profileTime("WindowsBar dismissSplashWhenReady done")
            }
        }
    }
}
