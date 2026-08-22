// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import QtQuick.Effects
import "../navigation"
import "../controls/navigation"
import "../controls/data"
import "../controls/feedback"
import ".."

// WindowsFilled - Vertical split navigation window 垂直分割导航窗口
// Left: title bar + navigation, Right: content area 左侧：标题栏+导航，右侧：内容区
NavigationWindowCore {
    id: window

    // ==================== Public Props 公开属性 ====================
    default property list<QtObject> pages
    property var pageSources: []

    windowTitle: ""

    // Use left layout mode. 使用左侧布局模式。
    titleBarPosition: Enums.windowType.title_bar_left
    leftPanelWidth: Math.max(navigationBar.implicitWidth, Enums.window.navPanelMinWidth)

    // Override the base navigation reference. 覆盖基类导航引用。
    navigationView: navigationBar

    // Left panel content. 左侧面板内容。
    leftPanelContent: [
        ToggleNavigationBar {
            id: navigationBar
            anchors.fill: parent
            model: window.navigationItems
            bottomItems: window.bottomNavigationItems
            smoothScroll: window.navigationSmoothScroll
            scrollDuration: window.navigationScrollDuration
            scrollStep: window.navigationScrollStep
            backgroundColor: window._micaActive ? Enums.transparent : Enums.backgroundColor
            // Bind window.currentIndex to the navigation bar in one direction.
            // 单向绑定 window.currentIndex 到导航栏，setCurrentIndex 只需修改窗口状态。
            currentIndex: window.currentIndex

            onItemClicked: (index) => {
                window.currentIndex = index
                window.currentPageChanged(index)
            }
            onBottomItemClicked: (index) => {
                window._handleBottomItemClicked(index, navigationBar, window.stackedWidget, window.pageSources)
            }
        }
    ]
    
    // Content area. 内容区域。
    content: Rectangle {
        anchors.fill: parent
        color: window.contentBgColor
        
        WindowsFilledStartupTimer {
            id: startupTimer
            targetLoader: mainLoader
        }
        
        Loader {
            id: mainLoader
            objectName: "windowsFilledCoreLoader"
            anchors.fill: parent
            active: false
            asynchronous: true
            sourceComponent: contentComponent
            
            onLoaded: {
                window.stackedWidget = item.stackAlias
                
                try {
                    if (window.pages.length > 0) {
                        window._moveDefaultPages(
                            window.pages,
                            window.stackedWidget.containerItem,
                            "WindowsFilled"
                        )
                    }
                } finally {
                    // Dismiss the splash after the home page is ready, not after the shell alone. 首页就绪后再关闭欢迎页，而不是仅等待框架壳。
                    window._dismissSplashWhenReady(window.stackedWidget)
                }
            }
        }
        
        Component {
            id: contentComponent
            Item {
                // alias 指向 helper 自己的 alias，一级目标合法 alias→alias is legal
                property alias stackAlias: pageStack.stackAlias

                anchors.fill: parent

        // Clear input focus from blank space. 点击空白区域清除输入焦点。
        MouseArea {
            anchors.fill: parent
            z: Enums.zIndex.background
            onClicked: parent.forceActiveFocus()
        }
        
        // Page stack and lazy-loading overlay 页面栈与懒加载覆盖层
        WindowsPageStack {
            id: pageStack

            host: window
            // ToggleNavigationBar 是 Item，没有 indicatorAnimationEnabled，此处恒为
            // false。原代码用三元表达式把 undefined 吞成 falsy，行为相同；这里显式
            // 布尔化以满足 required bool。修不修是单独议题，不并入本次去重。
            // ToggleNavigationBar lacks the property, so this is always false, matching
            // the ternary's undefined-to-falsy coercion before the extraction.
            navAnimationEnabled: !!navigationBar.indicatorAnimationEnabled
            overlayActive: window._pythonLoading
            overlayText: window.loadingText
        }
        }
    }
}
}
