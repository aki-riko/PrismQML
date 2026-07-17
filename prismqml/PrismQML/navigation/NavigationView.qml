// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/icons"

// NavigationView - Fluent Design expandable sidebar navigation (Window style)
// Horizontal layout (icon+text), supports expand/collapse
// Extends NavigationPanelCore for common indicator/routing logic
NavigationPanelCore {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property bool showReturnButton: true
    property bool isExpanded: false

    // ==================== Internal Props 内部属性 ====================
    // Maps key to page index for bottom page items
    property var _bottomPageIndexMap: ({})

    // ==================== Readonly State 只读状态 ====================
    readonly property bool isCompact: !isExpanded
    readonly property int compactButtonWidth: Enums.controlSize.navPanelCompactWidth - Enums.controlSize.navPanelPaddingH * 2

    // ==================== Signals 信号 ====================
    signal returnButtonClicked()
    signal currentItemUpdated(string key)
    signal aboutToExpand()  // Emitted before expanding, for acrylic grab 展开前发射，用于截图

    // ==================== Public Methods 公开方法 ====================
    function expand() {
        if (!isExpanded) {
            aboutToExpand()
        }
        isExpanded = true
    }
    function collapse() { isExpanded = false }
    function toggle() {
        if (!isExpanded) {
            aboutToExpand()
        }
        isExpanded = !isExpanded
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.navPanelExpandWidth
    implicitHeight: parent ? parent.height : 400

    // Override base class titleBarHeight 覆盖基类的标题栏高度
    titleBarHeight: Enums.window.titleBarHeight
    // Indicator config 指示器配置
    indicatorX: Enums.controlSize.navPanelPaddingH
    indicatorWidth: Enums.controlSize.navIndicatorWidth
    indicatorHeight: Enums.controlSize.navIndicatorHeight
    // Connect repeaters 连接 Repeater
    topRepeater: topRep
    bottomRepeater: bottomRep

    // Forward signal 转发信号
    onCurrentItemChanged: (key) => currentItemUpdated(key)

    // ==================== Content 内容 ====================
    // Return button 返回按钮
    Rectangle {
        id: returnBtn

        readonly property int iconCenterMargin: (control.compactButtonWidth - Enums.iconSize.s) / 2

        visible: control.showReturnButton
        anchors.top: parent.top
        anchors.left: parent.left
        // Top margin includes title bar height to align with title text 顶部边距包含标题栏高度，与标题文字对齐
        anchors.topMargin: control.titleBarHeight + Enums.controlSize.navPanelPaddingV
        anchors.leftMargin: Enums.controlSize.navPanelPaddingH
        width: control.compactButtonWidth  // Always compact width 始终紧凑宽度
        height: Enums.controlSize.navItemHeight
        radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.card
        color: returnArea.containsMouse ? Enums.stateColor.hover : Enums.transparent
        
        Row {
            anchors.left: parent.left
            anchors.leftMargin: returnBtn.iconCenterMargin
            anchors.verticalCenter: parent.verticalCenter
            spacing: Enums.spacing.l
            
            Icon {
                iconSize: Enums.iconSize.s
                icon: Enums.icon.arrow_left
            }
        }
        
        MouseArea {
            id: returnArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: control.returnButtonClicked()
        }
    }
    
    // Menu button (collapse/expand) 菜单按钮（折叠/展开）
    Rectangle {
        id: menuBtn

        readonly property int iconCenterMargin: (control.compactButtonWidth - Enums.iconSize.m) / 2

        anchors.top: returnBtn.visible ? returnBtn.bottom : parent.top
        anchors.topMargin: returnBtn.visible ? Enums.controlSize.navItemSpacing : (control.titleBarHeight + Enums.controlSize.navPanelPaddingV)
        anchors.left: parent.left
        anchors.leftMargin: Enums.controlSize.navPanelPaddingH
        width: control.compactButtonWidth  // Always compact width 始终紧凑宽度
        height: Enums.controlSize.navItemHeight
        radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.card
        color: menuArea.containsMouse ? Enums.stateColor.hover : Enums.transparent
        
        Icon {
            anchors.left: parent.left
            anchors.leftMargin: menuBtn.iconCenterMargin
            anchors.verticalCenter: parent.verticalCenter
            iconSize: Enums.iconSize.m
            icon: Enums.icon.navigation
        }
        
        MouseArea {
            id: menuArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: control.toggle()
        }
    }
    
    // Top navigation items 顶部导航项
    Column {
        id: topLayout
        anchors.top: menuBtn.bottom
        anchors.left: parent.left
        anchors.topMargin: Enums.controlSize.navItemSpacing
        anchors.leftMargin: Enums.controlSize.navPanelPaddingH
        width: control.isCompact ? control.compactButtonWidth : (parent.width - Enums.controlSize.navPanelPaddingH * 2)
        spacing: Enums.controlSize.navItemSpacing
        
        Repeater {
            id: topRep
            model: control.model
            
            delegate: NavigationViewItem {
                width: parent.width
                text: modelData.text || ""
                icon: modelData.icon || ""
                selected: index === control.currentIndex
                compact: control.isCompact
                
                onClicked: control._onItemClicked(index, false)
            }
        }
    }
    
    // Bottom fixed items 底部固定项
    Column {
        id: bottomLayout
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.bottomMargin: Enums.controlSize.navPanelPaddingV
        anchors.leftMargin: Enums.controlSize.navPanelPaddingH
        width: control.isCompact ? control.compactButtonWidth : (parent.width - Enums.controlSize.navPanelPaddingH * 2)
        spacing: Enums.controlSize.navItemSpacing
        
        Repeater {
            id: bottomRep
            model: control.bottomItems
            
            delegate: NavigationViewItem {
                width: parent.width
                text: modelData.text || ""
                icon: modelData.icon || ""
                // Bottom page items use key to find page index 底部页面项通过 key 查找页面索引来判断渲染状态
                selected: {
                    var item = control.bottomItems[index]
                    var hasKey = item && item.key !== undefined
                    var isSelectable = item && item.selectable !== false
                    if (hasKey && isSelectable) {
                        // Page item: check if current page matches key 页面项：检查当前页面是否匹配 key
                        return control.currentIndex === control._bottomPageIndexMap[item.key]
                    }
                    return false  // Function items are never selected 功能项永不选中
                }
                compact: control.isCompact
                selectable: modelData.selectable !== false
                
                onClicked: {
                    // Always emit signal, let window handle page switch 始终发送信号，让窗口组件处理页面切换
                    control.bottomItemClicked(index)
                }
            }
        }
    }
}
