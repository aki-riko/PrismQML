// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import QtQuick.Effects
import "../navigation"
import "../controls/navigation"
import "../controls/data"
import ".."

// WindowsFilled - Vertical split navigation window 垂直分割导航窗口
// Left: title bar + navigation, Right: content area 左侧：标题栏+导航，右侧：内容区
NavigationWindowCore {
    id: window

    // ==================== Public Props 公开属性 ====================
    default property alias pages: _hiddenStack.data
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
        
        Timer {
            id: startupTimer
            interval: Enums.window.splitStartupDelayMs
            running: true
            onTriggered: mainLoader.active = true
        }
        
        Loader {
            id: mainLoader
            anchors.fill: parent
            active: false
            asynchronous: true
            sourceComponent: contentComponent
            
            onLoaded: {
                window.stackedWidget = item.stackAlias
                
                if (_hiddenStack.data.length > 0) {
                    let container = window.stackedWidget.containerItem
                    let items = []
                    for(let i=0; i<_hiddenStack.data.length; i++) {
                        items.push(_hiddenStack.data[i])
                    }
                    for(let i=0; i<items.length; i++) {
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
                }
                
                // Dismiss the splash after the home page is ready, not after the shell alone. 首页就绪后再关闭欢迎页，而不是仅等待框架壳。
                window._dismissSplashWhenReady(window.stackedWidget)
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
            pageSources: window.pageSources
            lazyLoading: window.lazyLoading
            // Bind window.currentIndex to stack.currentIndex in one direction.
            // 单向绑定 window.currentIndex 到 stack.currentIndex；内部显示由 _displayIndex 驱动。
            currentIndex: window.currentIndex
            onCurrentChanged: (index) => {
                // Synchronize back after animation when needed. 动画结束后按需反向同步。
                if (window.currentIndex !== index) window.currentIndex = index
            }
        }
        
        // Python lazy-loading overlay. Python 懒加载覆盖层。
        LoadingOverlay {
            anchors.fill: parent
            loading: window._pythonLoading
            backgroundColor: window.contentBgColor
            text: window.loadingText
        }
        }
    }
}

    // Preserve default-property pages in a hidden staging item. 在隐藏暂存项中保留 default property 页面。
    Item { id: _hiddenStack; visible: false }
}
