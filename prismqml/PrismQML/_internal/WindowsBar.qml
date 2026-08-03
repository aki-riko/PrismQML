// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// WindowsBar - Top navigation window bar 顶部导航窗口栏
// Extends NavigationWindowCore with a vertical icon-and-text NavigationBar.
// 使用纵向图标与文字 NavigationBar 扩展 NavigationWindowCore。
NavigationWindowCore {
    id: window

    // ==================== Public Props 公开属性 ====================
    default property list<QtObject> pages
    property int contentTopMargin: Enums.spacing.none
    property var pageSources: []

    windowTitle: ""
    titleBarHeight: Enums.spacing.xxxl * 2
    titleBarLeftMargin: Enums.spacing.xxl

    Component.onCompleted: window.profileDetail(
        "WindowsBar root completed nav=" + _safeNavigationItems.length +
        " bottom=" + _safeBottomNavigationItems.length +
        " staged=" + pages.length
    )

    // Content layout. 内容布局。
    content: Item {
        anchors.fill: parent
        Component.onCompleted: window.profileDetail("WindowsBar content shell completed")

        Timer {
            id: startupTimer
            interval: Enums.duration.none
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

                try {
                    if (window.pages.length > 0) {
                        window.profileTime("WindowsBar move staged pages start count=" + window.pages.length)
                        window._moveDefaultPages(
                            window.pages,
                            window.stackedWidget.containerItem,
                            "WindowsBar"
                        )
                        window.profileTime("WindowsBar move staged pages done")
                    }
                } finally {
                    window.profileTime("WindowsBar dismissSplashWhenReady start")
                    window._dismissSplashWhenReady(window.stackedWidget)
                    window.profileTime("WindowsBar dismissSplashWhenReady done")
                }
            }
        }
    }

}
