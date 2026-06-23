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

// WindowsBar - Top navigation window bar
// Extends NavigationWindowCore with NavigationBar (icon+text vertical) 继承NavigationWindowCore
NavigationWindowCore {
    id: window
    
    windowTitle: ""
    titleBarHeight: Enums.spacing.xxxl * 2
    titleBarLeftMargin: Enums.spacing.xxl
    
    // ==================== Compact Navigation Props 紧凑导航属性 ====================
    property int contentTopMargin: Enums.spacing.none

    // ==================== Lazy Loading Aliases 懒加载别名 ====================
    property list<Component> pageComponents
    property var pageSources: []

    Item { id: _hiddenStack; visible: false }
    default property alias pages: _hiddenStack.data

    // ==================== Content Layout ====================
    content: Item {
        anchors.fill: parent
        
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
                window.navigationView = item.navAlias
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
                property alias navAlias: navigationBar
                property alias stackAlias: stack
                
        // 点击空白区域清除输入焦点（z极低，确保在所有内容之下）
        MouseArea {
            anchors.fill: parent
            z: -999
            onClicked: parent.forceActiveFocus()
        }
        
        NavigationBar {
            id: navigationBar
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.topMargin: contentTopMargin
            anchors.bottom: parent.bottom
            model: window.navigationItems
            bottomItems: window.bottomNavigationItems
            // Mica active: transparent to show Mica, Mica inactive: opaque background 云母激活：透明显示云母，云母关闭：不透明背景

            backgroundColor: window._micaActive ? Enums.transparent : Enums.backgroundColor
            // 单向绑定 window.currentIndex → navigationBar.currentIndex
            currentIndex: window.currentIndex


            onItemClicked: (index) => {
                window.currentIndex = index
                window.currentPageChanged(index)
            }
            onBottomItemClicked: (index) => {
                window._handleBottomItemClicked(index, navigationBar, stack, window.pageSources)
            }
        }

        ContentFrame {
            id: contentFrame
            anchors.left: navigationBar.right
            anchors.top: parent.top
            anchors.topMargin: contentTopMargin
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            backgroundColor: window.contentBgColor
            cornerRadius: window.contentCornerRadius

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
                    if (window.currentIndex !== index) window.currentIndex = index
                }
            }
            
            // Python lazy loading overlay Python 懒加载覆盖层
            LoadingOverlay {
                anchors.fill: parent
                loading: window._pythonLoading
                backgroundColor: window.contentBgColor
                text: window.loadingText
            }
        }
        
        Row {
            anchors.left: navigationBar.right
            anchors.leftMargin: Enums.spacing.xxxl
            anchors.top: parent.top
            anchors.bottom: contentFrame.top
            spacing: Enums.spacing.l
            
            Item {
                width: Enums.iconSize.l; height: Enums.iconSize.l
                anchors.verticalCenter: parent.verticalCenter
                visible: false
            }
            Label {
                text: ""
                type: Enums.label.type_body_strong
                color: Enums.textColor.primary
                anchors.verticalCenter: parent.verticalCenter
                visible: text !== ""
            }
        }
        }
    }
}

}
