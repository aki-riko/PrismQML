// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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

    windowTitle: ""
    
    // Use left layout mode 使用左侧布局模式
    titleBarPosition: Enums.windowType.title_bar_left
    leftPanelWidth: Math.max(navigationBar.implicitWidth, Enums.window.navPanelMinWidth)
    
    // Override base refs 覆盖基类引用
    navigationView: navigationBar
    stackedWidget: stack

    // ==================== Lazy Loading Aliases 懒加载别名 ====================
    property list<Component> pageComponents
    property var pageSources: []

    // ==================== Toggle Style Props ====================
    Item { id: _hiddenStack; visible: false }
    default property alias pages: _hiddenStack.data

    // ==================== Left Panel Content 左侧面板内容 ====================
    leftPanelContent: [
        ToggleNavigationBar {
            id: navigationBar
            anchors.fill: parent
            model: window.navigationItems
            bottomItems: window.bottomNavigationItems
            backgroundColor: window._micaActive ? Enums.transparent : Enums.backgroundColor
            // 单向绑定 window.currentIndex → navigationBar.currentIndex
            // 任何 setCurrentIndex 调用只需改 window.currentIndex,这里自然跟随
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
    
    // ==================== Content Area 内容区域 ====================
    content: Rectangle {
        anchors.fill: parent
        color: window.contentBgColor
        
        Timer {
            id: startupTimer
            interval: 50
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
                
                // 等主页(首屏)真正加载完成再关欢迎页, 而非框架壳加载完就关
                window._dismissSplashWhenReady(window.stackedWidget)
            }
        }
        
        Component {
            id: contentComponent
            Item {
                anchors.fill: parent
                property alias stackAlias: stack

        // 点击空白区域清除输入焦点
        MouseArea {
            anchors.fill: parent
            z: Enums.zIndex.background
            onClicked: parent.forceActiveFocus()
        }
        
        StackedWidget {
            id: stack
            anchors.fill: parent
            animationType: Enums.animation.popup
            property alias contentContainerAlias: stack.content
            pageComponents: window.pageComponents
            pageSources: window.pageSources
            lazyLoading: window.lazyLoading
            // 单向绑定 window.currentIndex → stack.currentIndex
            // currentIndex 为纯输入, StackedWidget 内部不再命令式写它
            // (改用 _displayIndex 驱动显示), 故声明式绑定不会被打破。
            currentIndex: window.currentIndex
            onCurrentChanged: (index) => {
                // 反向同步 (动画结束后) — 用户点击 navigationBar 后 window.currentIndex
                // 已经设过, 这里幂等; 但保留兼容旧路径
                if (window.currentIndex !== index) window.currentIndex = index
            }
        }
        
        // Python lazy loading overlay Python懒加载覆盖层
        LoadingOverlay {
            anchors.fill: parent
            loading: window._pythonLoading
            backgroundColor: window.contentBgColor
            text: window.loadingText
        }
        }
    }
}
}
