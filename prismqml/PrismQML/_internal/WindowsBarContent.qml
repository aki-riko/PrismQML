// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../navigation"
import "../controls/navigation"
import "../controls/feedback"
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
            hostWindow.profileTime("WindowsBar contentComponent completed compactNav=" + _compactNav)
        }
    }

    MouseArea {
        anchors.fill: parent
        z: Enums.zIndex.background
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
        model: root.hostWindow && !root._compactNav
            ? root.hostWindow.navigationItems : []
        bottomItems: root.hostWindow && !root._compactNav
            ? root.hostWindow.bottomNavigationItems : []
        smoothScroll: root.hostWindow ? root.hostWindow.navigationSmoothScroll : true
        scrollDuration: root.hostWindow ? root.hostWindow.navigationScrollDuration : Enums.duration.navigationScroll
        scrollStep: root.hostWindow ? root.hostWindow.navigationScrollStep : Enums.spacing.navigationScrollStep
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

            onItemClicked: (index) => {
                if (!root.hostWindow) return
                root.hostWindow.currentIndex = index
                root.hostWindow.currentPageChanged(index)
            }
        }
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

            onCurrentChanged: (index) => {
                if (root.hostWindow && root.hostWindow.currentIndex !== index) {
                    root.hostWindow.currentIndex = index
                }
            }
            onPythonLazyCollapseFinished: (index) => {
                if (root.hostWindow) {
                    root.hostWindow._handlePythonLazyCollapseFinished(index)
                }
            }
            onPythonLazyExpansionStarted: (index) => {
                if (root.hostWindow) {
                    root.hostWindow._beginPythonLoadingVisualExit(index)
                }
            }
            onPythonLazyTransitionFinished: (index) => {
                if (root.hostWindow) {
                    root.hostWindow._completePythonLoadingVisual(index)
                }
            }
        }

        Loader {
            id: loadingOverlayLoader

            property bool transitionActive: false

            objectName: "loadingOverlayLoader"
            anchors.fill: parent
            active: root._loadingOverlayActive || transitionActive
            asynchronous: false
            onLoaded: {
                transitionActive = false
                if (root.hostWindow) {
                    root.hostWindow._pythonLoadingOverlay = item
                    root.hostWindow._handlePythonLoadingOverlayReady()
                }
            }
            onItemChanged: {
                if (!item) {
                    transitionActive = false
                    if (root.hostWindow) root.hostWindow._pythonLoadingOverlay = null
                }
            }
            sourceComponent: QMLPage {
                property bool loading: root._loadingOverlayActive

                objectName: "loadingOverlay"
                backgroundColor: Enums.transparent
                running: visible && !finishing
                text: {
                    Translator._v
                    return root.hostWindow ? root.hostWindow.loadingText : Translator.tr("loading")
                }
                Component.onCompleted: if (loading) start()
                onLoadingChanged: {
                    if (loading) start()
                    else finish()
                }
            }

            Connections {
                function onFinishingChanged() {
                    loadingOverlayLoader.transitionActive = target.finishing
                }

                target: loadingOverlayLoader.item
                ignoreUnknownSignals: true
            }
        }
    }
}
