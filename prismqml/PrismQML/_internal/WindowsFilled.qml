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
                property alias stackAlias: stack

                anchors.fill: parent

        // Clear input focus from blank space. 点击空白区域清除输入焦点。
        MouseArea {
            anchors.fill: parent
            z: Enums.zIndex.background
            onClicked: parent.forceActiveFocus()
        }
        
        StackedWidget {
            id: stack
            property alias contentContainerAlias: stack.content

            anchors.fill: parent
            animationType: Enums.animation.popup
            lazyActivationDelay: navigationBar.indicatorAnimationEnabled
                ? Enums.duration.dialog : Enums.duration.none
            pageSources: window.pageSources
            lazyLoading: window.lazyLoading
            _pythonPageMode: window._pythonPageMode
            // Bind window.currentIndex to stack.currentIndex in one direction.
            // 单向绑定 window.currentIndex 到 stack.currentIndex；内部显示由 _displayIndex 驱动。
            currentIndex: window.currentIndex
            onCurrentChanged: (index) => {
                // Synchronize back after animation when needed. 动画结束后按需反向同步。
                if (window.currentIndex !== index) window.currentIndex = index
            }
            onPythonLazyCollapseFinished: (index) => {
                window._handlePythonLazyCollapseFinished(index)
            }
            onPythonLazyExpansionStarted: (index) => {
                window._beginPythonLoadingVisualExit(index)
            }
            onPythonLazyTransitionFinished: (index) => {
                window._completePythonLoadingVisual(index)
            }
        }
        
        // Python lazy-loading overlay. Python 懒加载覆盖层。
        Loader {
            id: loadingOverlayLoader

            property bool transitionActive: false

            objectName: "loadingOverlayLoader"
            anchors.fill: parent
            active: window._pythonLoading || transitionActive
            asynchronous: false
            onLoaded: {
                transitionActive = false
                window._pythonLoadingOverlay = item
                window._handlePythonLoadingOverlayReady()
            }
            onItemChanged: {
                if (!item) {
                    transitionActive = false
                    window._pythonLoadingOverlay = null
                }
            }
            sourceComponent: QMLPage {
                property bool loading: window._pythonLoading

                objectName: "loadingOverlay"
                backgroundColor: Enums.transparent
                running: visible && !finishing
                text: window.loadingText
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
}
}
