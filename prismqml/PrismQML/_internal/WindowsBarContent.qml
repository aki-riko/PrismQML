// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../navigation"
import "../controls/navigation"
import ".."

// WindowsBarContent - Deferred compact navigation window content
Item {
    id: root

    // ==================== Host Props ====================
    property var hostWindow: null
    property int contentTopMargin: 0
    property alias navAlias: navigationBar
    property alias stackAlias: stack

    readonly property bool _compactNav:
        typeof PlatformInfo !== "undefined" && PlatformInfo.isCompact

    anchors.fill: parent

    Component.onCompleted: {
        if (hostWindow) {
            hostWindow.profileTime("WindowsBar contentComponent completed compactNav=" + _compactNav)
        }
    }

    MouseArea {
        anchors.fill: parent
        z: -999
        onClicked: parent.forceActiveFocus()
    }

    NavigationBar {
        id: navigationBar
        objectName: "navigationBar"
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.topMargin: root.contentTopMargin
        anchors.bottom: parent.bottom
        visible: !root._compactNav
        width: root._compactNav ? 0 : implicitWidth
        model: root.hostWindow ? root.hostWindow.navigationItems : []
        bottomItems: root.hostWindow ? root.hostWindow.bottomNavigationItems : []
        backgroundColor: root.hostWindow && root.hostWindow._micaActive
            ? Enums.transparent
            : Enums.backgroundColor
        currentIndex: root.hostWindow ? root.hostWindow.currentIndex : 0

        onItemClicked: (index) => {
            if (!root.hostWindow) return
            root.hostWindow.currentIndex = index
            root.hostWindow.currentPageChanged(index)
        }
        onBottomItemClicked: (index) => {
            if (!root.hostWindow) return
            root.hostWindow._handleBottomItemClicked(index, navigationBar, stack, root.hostWindow.pageSources)
        }
    }

    BottomTabBar {
        id: bottomTabBar
        objectName: "bottomTabBar"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        visible: root._compactNav
        model: root.hostWindow ? root.hostWindow.navigationItems : []
        currentIndex: root.hostWindow ? root.hostWindow.currentIndex : 0

        onItemClicked: (index) => {
            if (!root.hostWindow) return
            root.hostWindow.currentIndex = index
            root.hostWindow.currentPageChanged(index)
        }
    }

    ContentFrame {
        id: contentFrame
        anchors.left: root._compactNav ? parent.left : navigationBar.right
        anchors.top: parent.top
        anchors.topMargin: root.contentTopMargin
        anchors.right: parent.right
        anchors.bottom: root._compactNav ? bottomTabBar.top : parent.bottom
        backgroundColor: root.hostWindow ? root.hostWindow.contentBgColor : Enums.stateColor.contentBg
        cornerRadius: root.hostWindow ? root.hostWindow.contentCornerRadius : Enums.radius.large

        StackedWidget {
            id: stack
            anchors.fill: parent
            animationType: Enums.animation.popup
            property alias contentContainerAlias: stack.content
            pageComponents: root.hostWindow ? root.hostWindow.pageComponents : []
            pageSources: root.hostWindow ? root.hostWindow.pageSources : []
            lazyLoading: root.hostWindow ? root.hostWindow.lazyLoading : false
            currentIndex: root.hostWindow ? root.hostWindow.currentIndex : 0

            onCurrentChanged: (index) => {
                if (root.hostWindow && root.hostWindow.currentIndex !== index) {
                    root.hostWindow.currentIndex = index
                }
            }
        }

        LoadingOverlay {
            anchors.fill: parent
            loading: root.hostWindow ? root.hostWindow._pythonLoading : false
            backgroundColor: root.hostWindow ? root.hostWindow.contentBgColor : Enums.stateColor.contentBg
            text: root.hostWindow ? root.hostWindow.loadingText : Translator.tr("loading")
        }
    }
}
