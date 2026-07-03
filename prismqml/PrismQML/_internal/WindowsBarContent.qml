// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// WindowsBarContent - Deferred compact navigation window content
Item {
    id: root

    // ==================== Host Props ====================
    property var hostWindow: null
    property int contentTopMargin: 0
    property alias stackAlias: stack
    property var navAlias: navigationLoader.item || bottomTabLoader.item

    // ==================== Internal Props 内部属性 ====================
    property bool _navigationActive: false
    property bool _navigationLoadScheduled: false

    readonly property bool _compactNav:
        typeof PlatformInfo !== "undefined" && PlatformInfo.isCompact

    // ==================== Signals 信号 ====================
    signal navigationReady(var navigationView)

    // ==================== Internal Methods 内部方法 ====================
    function _scheduleNavigationLoad() {
        if (_navigationLoadScheduled) return
        _navigationLoadScheduled = true

        var splash = root.hostWindow ? root.hostWindow._splashInstance : null
        if (splash && splash.visible && splash.finished) {
            if (root.hostWindow) {
                root.hostWindow.profileTime("WindowsBarContent navigation waits for splash.finished")
            }
            splash.finished.connect(root._startNavigationDelay)
            return
        }
        _startNavigationDelay()
    }

    function _startNavigationDelay() {
        if (_navigationActive) return
        navigationDelayTimer.restart()
    }

    function _activateNavigation() {
        if (_navigationActive) return
        _navigationActive = true
        if (root.hostWindow) {
            root.hostWindow.profileTime("WindowsBarContent deferred navigation activated compactNav=" + _compactNav)
        }
    }

    function _publishNavigationReady(item, label) {
        if (!item) return
        if (root.hostWindow) {
            root.hostWindow.profileTime("WindowsBarContent " + label + " ready")
        }
        navigationReady(item)
    }

    function _configureNavigationBar(item) {
        if (!item) return

        item.objectName = "navigationBar"
        item.model = Qt.binding(function() { return root.hostWindow ? root.hostWindow.navigationItems : [] })
        item.bottomItems = Qt.binding(function() { return root.hostWindow ? root.hostWindow.bottomNavigationItems : [] })
        item.backgroundColor = Qt.binding(function() {
            return root.hostWindow && root.hostWindow._micaActive
                ? Enums.transparent
                : Enums.backgroundColor
        })
        item.currentIndex = Qt.binding(function() { return root.hostWindow ? root.hostWindow.currentIndex : 0 })
        item.itemClicked.connect(root._handleNavigationItemClicked)
        item.bottomItemClicked.connect(root._handleNavigationBottomItemClicked)

        if (root.hostWindow) {
            root.hostWindow.profileDetail("NavigationBar completed deferred visible=" + item.visible + " width=" + item.width)
        }
        _publishNavigationReady(item, "NavigationBar")
    }

    function _configureBottomTabBar(item) {
        if (!item) return

        item.objectName = "bottomTabBar"
        item.model = Qt.binding(function() { return root.hostWindow ? root.hostWindow.navigationItems : [] })
        item.currentIndex = Qt.binding(function() { return root.hostWindow ? root.hostWindow.currentIndex : 0 })
        item.window_micaActiveFallback = Qt.binding(function() {
            return root.hostWindow ? root.hostWindow._micaActive : false
        })
        item.itemClicked.connect(root._handleNavigationItemClicked)

        if (root.hostWindow) {
            root.hostWindow.profileDetail("BottomTabBar completed deferred visible=" + item.visible)
        }
        _publishNavigationReady(item, "BottomTabBar")
    }

    function _configureLoadingOverlay(item) {
        if (!item) return

        item.loading = Qt.binding(function() {
            return root.hostWindow ? root.hostWindow._pythonLoading : false
        })
        item.backgroundColor = Qt.binding(function() {
            return root.hostWindow ? root.hostWindow.contentBgColor : Enums.stateColor.contentBg
        })
        item.text = Qt.binding(function() {
            return root.hostWindow ? root.hostWindow.loadingText : Translator.tr("loading")
        })
        if (root.hostWindow) {
            root.hostWindow.profileDetail("LoadingOverlay completed deferred loading=" + item.loading)
        }
    }

    function _handleNavigationItemClicked(index) {
        if (!root.hostWindow) return
        root.hostWindow.currentIndex = index
        root.hostWindow.currentPageChanged(index)
    }

    function _handleNavigationBottomItemClicked(index) {
        if (!root.hostWindow || !navigationLoader.item) return
        root.hostWindow._handleBottomItemClicked(index, navigationLoader.item, stack, root.hostWindow.pageSources)
    }

    anchors.fill: parent

    Component.onCompleted: {
        if (hostWindow) {
            hostWindow.profileDetail(
                "WindowsBarContent root completed nav=" +
                (hostWindow.navigationItems ? hostWindow.navigationItems.length : 0) +
                " bottom=" +
                (hostWindow.bottomNavigationItems ? hostWindow.bottomNavigationItems.length : 0)
            )
            hostWindow.profileTime("WindowsBar contentComponent completed compactNav=" + _compactNav)
        }
        _scheduleNavigationLoad()
    }

    MouseArea {
        anchors.fill: parent
        z: -999
        onClicked: parent.forceActiveFocus()
        Component.onCompleted: if (root.hostWindow) root.hostWindow.profileDetail("WindowsBarContent focus MouseArea completed")
    }

    Item {
        id: navigationSlot
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.topMargin: root.contentTopMargin
        anchors.bottom: parent.bottom
        visible: !root._compactNav
        width: root._compactNav ? 0 : Enums.controlSize.navBarWidth

        Loader {
            id: navigationLoader
            anchors.fill: parent
            active: root._navigationActive && !root._compactNav
            asynchronous: true
            source: Qt.resolvedUrl("../navigation/NavigationBar.qml")
            onLoaded: root._configureNavigationBar(item)
        }
    }

    Item {
        id: bottomTabSlot
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        visible: root._compactNav
        height: root._compactNav
            ? (bottomTabLoader.item ? bottomTabLoader.item.implicitHeight : Enums.controlSize.bottomTabBarHeight)
            : 0

        Loader {
            id: bottomTabLoader
            anchors.fill: parent
            active: root._navigationActive && root._compactNav
            asynchronous: true
            source: Qt.resolvedUrl("../navigation/BottomTabBar.qml")
            onLoaded: root._configureBottomTabBar(item)
        }
    }

    ContentFrame {
        id: contentFrame
        anchors.left: root._compactNav ? parent.left : navigationSlot.right
        anchors.top: parent.top
        anchors.topMargin: root.contentTopMargin
        anchors.right: parent.right
        anchors.bottom: root._compactNav ? bottomTabSlot.top : parent.bottom
        backgroundColor: root.hostWindow ? root.hostWindow.contentBgColor : Enums.stateColor.contentBg
        cornerRadius: root.hostWindow ? root.hostWindow.contentCornerRadius : Enums.radius.large
        Component.onCompleted: if (root.hostWindow) root.hostWindow.profileDetail("ContentFrame completed")

        StackedWidget {
            id: stack
            anchors.fill: parent
            animationType: Enums.animation.popup
            property alias contentContainerAlias: stack.content
            pageComponents: root.hostWindow ? root.hostWindow.pageComponents : []
            pageSources: root.hostWindow ? root.hostWindow.pageSources : []
            lazyLoading: root.hostWindow ? root.hostWindow.lazyLoading : false
            currentIndex: root.hostWindow ? root.hostWindow.currentIndex : 0
            Component.onCompleted: if (root.hostWindow) root.hostWindow.profileDetail("WindowsBarContent StackedWidget instance completed count=" + count)

            onCurrentChanged: (index) => {
                if (root.hostWindow && root.hostWindow.currentIndex !== index) {
                    root.hostWindow.currentIndex = index
                }
            }
        }

        Loader {
            id: loadingOverlayLoader
            anchors.fill: parent
            active: root.hostWindow ? root.hostWindow._pythonLoading : false
            asynchronous: true
            source: active ? Qt.resolvedUrl("LoadingOverlay.qml") : ""
            onLoaded: root._configureLoadingOverlay(item)
        }
    }

    Timer {
        id: navigationDelayTimer
        interval: Enums.duration.instant
        onTriggered: root._activateNavigation()
    }
}
