// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/icons"
import "_internal"

// NavigationView - Fluent Design expandable sidebar navigation (Window style)
// Horizontal layout (icon+text), supports expand/collapse
// Extends NavigationPanelCore for common indicator/routing logic
NavigationPanelCore {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property bool showReturnButton: true
    property bool isExpanded: false
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.navigationScroll
    property real scrollStep: Enums.spacing.navigationScrollStep
    // Fade items near an overflowing edge to hint the list scrolls 溢出端渐隐以提示可滚动
    property bool scrollFadeEnabled: true

    // ==================== Internal Props 内部属性 ====================
    // Maps key to page index for bottom page items
    property var _bottomPageIndexMap: ({})

    // ==================== Readonly State 只读状态 ====================
    readonly property bool isCompact: !isExpanded
    readonly property int compactButtonWidth: Enums.controlSize.navPanelCompactWidth - Enums.controlSize.navPanelPaddingH * 2
    // 选中项的渐隐值; 底部固定项不在滚动区内, 不参与渐隐。
    readonly property real _selectedItemFade: scrollFade.selectionOpacity(
        control._getItemAt(control.currentIndex),
        control.currentIndex >= 0
            && control.currentIndex < (control._safeModel || []).length)

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
    function smoothScrollTo(targetY) { topScrollBehavior.scrollTo(targetY) }
    function smoothScrollBy(delta) { topScrollBehavior.scrollBy(delta) }

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

    // Bind scroll offset for real-time indicator tracking 绑定滚动偏移以实时跟踪指示器
    scrollOffset: topFlickable.contentY
    // 指示器裁剪下界 = 可滚动区底边, 滚动时指示器溢出此处被裁, 不露进底部固定项区。
    indicatorClipBottom: topFlickable.y + topFlickable.height
    // Keep the indicator in lockstep with the item it marks 指示器与所标记的项锁步渐隐
    indicatorOpacity: control._selectedItemFade

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
        radius: Enums.radius.card
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
        radius: Enums.radius.card
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
    
    // Edge fade state shared by the items and the indicator 导航项与指示器共用的渐隐状态
    NavigationScrollFade {
        id: scrollFade
        objectName: "navigationViewScrollFade"
        flickable: topFlickable
        active: control.scrollFadeEnabled
        itemHeight: Enums.controlSize.navItemHeight + Enums.controlSize.navItemSpacing
        itemCount: topRep.count
    }

    // Top navigation items (scrollable) 顶部导航项（可滚动）
    // 上界接菜单按钮, 下界停在底部固定项之前; 没有这层 Flickable 时超出面板高度的
    // 项会被裁掉且无法触达。
    // Bounded between the menu button and the fixed bottom items; without this
    // Flickable, items past the panel height were clipped and unreachable.
    Flickable {
        id: topFlickable
        anchors.top: menuBtn.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: Enums.controlSize.navItemSpacing
        anchors.leftMargin: Enums.controlSize.navPanelPaddingH
        anchors.rightMargin: Enums.controlSize.navPanelPaddingH
        height: Math.max(0, bottomLayout.y - topFlickable.y
                            - Enums.controlSize.navItemSpacing)

        contentWidth: width
        contentHeight: topLayout.height
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        interactive: false

        Column {
            id: topLayout
            width: control.isCompact ? control.compactButtonWidth : topFlickable.width
            spacing: Enums.controlSize.navItemSpacing

            Repeater {
                id: topRep
                model: control._safeModel

                delegate: NavigationViewItem {
                    width: parent.width
                    text: modelData ? (modelData.text || "") : ""
                    icon: modelData ? (modelData.icon || "") : ""
                    selected: index === control.currentIndex
                    compact: control.isCompact
                    opacity: scrollFade.opacityAt(y, height)

                    onClicked: control._onItemClicked(index, false)
                }
            }
        }

        NavigationSmoothScroll {
            id: topScrollBehavior
            helperName: "navigationViewSmoothScrollHelper"
            flickable: topFlickable
            smoothScroll: control.smoothScroll
            duration: control.scrollDuration
            step: control.scrollStep
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
            model: control._safeBottomItems
            
            delegate: NavigationViewItem {
                width: parent.width
                text: modelData ? (modelData.text || "") : ""
                icon: modelData ? (modelData.icon || "") : ""
                // Bottom page items use key to find page index 底部页面项通过 key 查找页面索引来判断渲染状态
                selected: {
                    var item = control._safeBottomItems[index]
                    var hasKey = item && item.key !== undefined
                    var isSelectable = item && item.selectable !== false
                    if (hasKey && isSelectable) {
                        // Page item: check if current page matches key 页面项：检查当前页面是否匹配 key
                        return control.currentIndex === control._bottomPageIndexMap[item.key]
                    }
                    return false  // Function items are never selected 功能项永不选中
                }
                compact: control.isCompact
                selectable: !modelData || modelData.selectable !== false
                
                onClicked: {
                    // Always emit signal, let window handle page switch 始终发送信号，让窗口组件处理页面切换
                    control.bottomItemClicked(index)
                }
            }
        }
    }
}
