// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../navigation"
import "../controls/navigation"
import ".."

// WindowsBarContent - Compact navigation window content 紧凑导航窗口内容
Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    property var hostWindow: null
    property int contentTopMargin: 0
    property alias navAlias: navigationBar
    property alias stackAlias: stack

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _compactNav:
        typeof PlatformInfo !== "undefined" && PlatformInfo && PlatformInfo.isCompact
    readonly property bool _loadingOverlayActive:
        !!(hostWindow && hostWindow._pythonLoading)

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
    }

    MouseArea {
        anchors.fill: parent
        z: Enums.zIndex.background
        onClicked: parent.forceActiveFocus()
        Component.onCompleted: if (root.hostWindow) root.hostWindow.profileDetail("WindowsBarContent focus MouseArea completed")
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
        smoothScroll: root.hostWindow ? root.hostWindow.navigationSmoothScroll : true
        scrollDuration: root.hostWindow ? root.hostWindow.navigationScrollDuration : Enums.duration.navigationScroll
        scrollStep: root.hostWindow ? root.hostWindow.navigationScrollStep : Enums.spacing.navigationScrollStep
        backgroundColor: root.hostWindow && root.hostWindow._micaActive
            ? Enums.transparent
            : Enums.backgroundColor
        currentIndex: root.hostWindow ? root.hostWindow.currentIndex : 0
        Component.onCompleted: if (root.hostWindow) root.hostWindow.profileDetail("NavigationBar completed visible=" + visible + " width=" + width)

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

    Loader {
        id: bottomTabBarLoader
        objectName: "bottomTabBar"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        active: root._compactNav
        visible: active
        asynchronous: false
        sourceComponent: BottomTabBar {
            objectName: "bottomTabBarContent"
            model: root.hostWindow ? root.hostWindow.navigationItems : []
            currentIndex: root.hostWindow ? root.hostWindow.currentIndex : 0
            window_micaActiveFallback: root.hostWindow ? root.hostWindow._micaActive : false
            Component.onCompleted: if (root.hostWindow) root.hostWindow.profileDetail("BottomTabBar completed visible=" + visible)

            onItemClicked: (index) => {
                if (!root.hostWindow) return
                root.hostWindow.currentIndex = index
                root.hostWindow.currentPageChanged(index)
            }
        }
        Component.onCompleted: if (root.hostWindow) root.hostWindow.profileDetail("BottomTabBar Loader completed active=" + active)
    }

    ContentFrame {
        id: contentFrame
        anchors.left: root._compactNav ? parent.left : navigationBar.right
        anchors.top: parent.top
        anchors.topMargin: root.contentTopMargin
        anchors.right: parent.right
        anchors.bottom: root._compactNav ? bottomTabBarLoader.top : parent.bottom
        backgroundColor: root.hostWindow ? root.hostWindow.contentBgColor : Enums.stateColor.contentBg
        cornerRadius: root.hostWindow ? root.hostWindow.contentCornerRadius : Enums.radius.large
        Component.onCompleted: if (root.hostWindow) root.hostWindow.profileDetail("ContentFrame completed")

        StackedWidget {
            id: stack
            property alias contentContainerAlias: stack.content

            anchors.fill: parent
            animationType: Enums.animation.popup
            lazyActivationDelay: navigationBar.indicatorAnimationEnabled
                ? Enums.duration.dialog : Enums.duration.none
            pageSources: root.hostWindow ? root.hostWindow.pageSources : []
            lazyLoading: root.hostWindow ? root.hostWindow.lazyLoading : false
            _pythonPageMode: root.hostWindow ? root.hostWindow._pythonPageMode : false
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
            active: root._loadingOverlayActive
            visible: active
            asynchronous: false
            sourceComponent: LoadingOverlay {
                loading: root._loadingOverlayActive
                backgroundColor: root.hostWindow ? root.hostWindow.contentBgColor : Enums.stateColor.contentBg
                text: {
                    Translator._v
                    return root.hostWindow ? root.hostWindow.loadingText : Translator.tr("loading")
                }
                Component.onCompleted: if (root.hostWindow) root.hostWindow.profileDetail("LoadingOverlay completed loading=" + loading)
            }
            Component.onCompleted: if (root.hostWindow) root.hostWindow.profileDetail("LoadingOverlay Loader completed active=" + active)
        }
    }
}
