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
    // alias 指向 helper 自己的 alias，一级目标合法 alias→alias is legal
    property alias stackAlias: pageStack.stackAlias

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _compactNav:
        typeof PlatformInfo !== "undefined" && PlatformInfo && PlatformInfo.isCompact
    readonly property bool _loadingOverlayActive:
        !!(hostWindow && hostWindow._pythonLoading)
    readonly property bool _usesWindowTicketPaper:
        !!hostWindow && Enums.isVintageTicket && !root._compactNav
    readonly property real _windowPaperOriginY:
        hostWindow && typeof hostWindow.titleBarHeight === "number"
        ? hostWindow.titleBarHeight + contentTopMargin : contentTopMargin

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
        backgroundColor: root._usesWindowTicketPaper
            ? Enums.transparent
            : (root.hostWindow && root.hostWindow._micaActive
                ? Enums.transparent : Enums.backgroundColor)
        currentIndex: root.hostWindow ? root.hostWindow.currentIndex : 0
        ticketPaperEnabled: !root._usesWindowTicketPaper
        paperOriginY: root._windowPaperOriginY

        onItemClicked: (index) => {
            if (!root.hostWindow) return
            root.hostWindow.currentIndex = index
            root.hostWindow.currentPageChanged(index)
        }

        onBottomItemClicked: (index) => {
            if (!root.hostWindow) return
            root.hostWindow._handleBottomItemClicked(
                index, navigationBar, pageStack.stackAlias, root.hostWindow.pageSources
            )
        }
    }

    // Complete the square ticket title divider across the navigation column.
    // 在导航列补齐方角票据标题分隔线，形成连续的 T 形接点。
    Rectangle {
        objectName: "ticketTitleDivider"
        anchors.left: parent.left
        anchors.top: parent.top
        width: navigationBar.width
        height: Enums.surfaceBorderWidth(Enums.border.thin)
        color: Enums.borderColor
        visible: Enums.isVintageTicket && !root._compactNav
        z: Enums.zIndex.controls
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
        backgroundColor: root._usesWindowTicketPaper
            ? Enums.transparent
            : (root.hostWindow ? root.hostWindow.contentBgColor : Enums.stateColor.contentBg)
        cornerRadius: root.hostWindow ? root.hostWindow.contentCornerRadius : Enums.radius.large
        ticketPaperEnabled: !root._usesWindowTicketPaper
        paperOriginX: root._compactNav ? 0 : navigationBar.width
        paperOriginY: root._windowPaperOriginY

        // Page stack and lazy-loading overlay 页面栈与懒加载覆盖层
        WindowsPageStack {
            id: pageStack

            // hostWindow may be null in this shell; the helper guards every access.
            // 本外壳的 hostWindow 可为 null，helper 内部对每次访问都做保护。
            host: root.hostWindow
            navAnimationEnabled: navigationBar.indicatorAnimationEnabled
            overlayActive: root._loadingOverlayActive
            // Translation dependency stays here. 翻译依赖留在本控件。
            overlayText: {
                Translator._v
                return root.hostWindow ? root.hostWindow.loadingText : Translator.tr("loading")
            }
        }
    }
}
