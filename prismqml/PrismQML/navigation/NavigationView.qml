// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/icons"
import "_internal"
import "_internal/NavigationLayout.js" as NavigationLayout

// NavigationView - Fluent Design expandable sidebar navigation (Window style) Fluent 可展开侧边导航 (Window 风格)
// Horizontal layout (icon+text), supports expand/collapse
// Extends NavigationPanelCore for common indicator/routing logic
NavigationPanelCore {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property bool showReturnButton: true
    property bool isExpanded: false
    // Pane display mode; pane_unspecified keeps isExpanded fully caller-owned
    // 面板显示模式; pane_unspecified 时 isExpanded 完全归调用方, 行为与历史一致
    property int paneDisplayMode: Enums.navigation.pane_unspecified
    // Minimal mode: the pane stays collapsed to the menu button until opened
    // 极简模式: 面板折叠到只剩菜单按钮, 打开后就地展开
    property bool isPaneOpen: false
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.navigationScroll
    property real scrollStep: Enums.spacing.navigationScrollStep
    // Fade items near an overflowing edge to hint the list scrolls 溢出端渐隐以提示可滚动
    property bool scrollFadeEnabled: true
    // Reveal a thin overlay rail on hover 悬停时显形细浮层滚动轨
    property bool scrollRailEnabled: true
    // Let touch and mouse drag scroll the list 允许触摸与鼠标拖拽滚动列表
    property bool dragScrollEnabled: true

    // ==================== Internal Props 内部属性 ====================
    // Maps key to page index for bottom page items
    property var _bottomPageIndexMap: ({})

    // ==================== Readonly State 只读状态 ====================
    readonly property bool isCompact: !isExpanded
    // Auto picks left while the pane can hold the expanded design width, else compact
    // 自动模式: 面板宽度装得下展开设计宽度时用 left, 否则用 compact
    readonly property int effectivePaneDisplayMode: {
        if (paneDisplayMode !== Enums.navigation.pane_auto) return paneDisplayMode
        return width >= Enums.controlSize.navPanelExpandWidth
            ? Enums.navigation.pane_left
            : Enums.navigation.pane_left_compact
    }
    readonly property bool minimalPane:
        effectivePaneDisplayMode === Enums.navigation.pane_left_minimal
    // Minimal keeps only the menu button while closed 极简模式关闭时只留菜单按钮
    readonly property bool itemsVisible: !(minimalPane && !isPaneOpen)
    // Rows are JS-created and only join the visual tree, so QObject-based findChildren
    // cannot see them; read instantiated rows through these accessors.
    // 条目由 JS 创建且只挂进视觉树, 基于 QObject 的 findChildren 看不到它们; 通过以下
    // 访问器读取已实例化条目。
    readonly property int itemCount: topRepeater ? topRepeater.count : 0
    readonly property int bottomItemCount: bottomRepeater ? bottomRepeater.count : 0
    readonly property int compactButtonWidth: Enums.controlSize.navPanelCompactWidth - Enums.controlSize.navPanelPaddingH * 2
    // Selected item fade value; pinned bottom items are outside the scroller 选中项的渐隐值; 底部固定项不在滚动区内, 不参与渐隐。
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
    // Instantiated top row at index, or null 已实例化的顶部条目, 越界返回 null
    function itemAt(index) {
        return topRepeater && index >= 0 && index < topRepeater.count
            ? topRepeater.itemAt(index) : null
    }
    // Instantiated pinned bottom row at index, or null 已实例化的底部固定条目
    function bottomItemAt(index) {
        return bottomRepeater && index >= 0 && index < bottomRepeater.count
            ? bottomRepeater.itemAt(index) : null
    }
    // Minimal-mode pane control 极简模式的面板开合
    function openPane() { isPaneOpen = true }
    function closePane() { isPaneOpen = false }
    function togglePane() { isPaneOpen = !isPaneOpen }

    // ==================== Internal Methods 内部方法 ====================
    // A display mode owns isExpanded, because "expanded" is exactly what the mode
    // decides. pane_unspecified opts out and leaves the caller's value untouched.
    // 显示模式接管 isExpanded —— "展开与否"正是模式要决定的事; pane_unspecified 例外,
    // 完全不动调用方的值。
    function _applyPaneDisplayMode() {
        var mode = effectivePaneDisplayMode
        if (mode === Enums.navigation.pane_unspecified) return
        if (mode === Enums.navigation.pane_left) {
            isExpanded = true
        } else if (mode === Enums.navigation.pane_left_compact) {
            isExpanded = false
        } else if (mode === Enums.navigation.pane_left_minimal) {
            isExpanded = isPaneOpen
        }
    }

    onItemCountChanged: Qt.callLater(control._initIndicatorPosition)
    onBottomItemCountChanged: Qt.callLater(control._initIndicatorPosition)

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
    // Indicator clip bottom = scrollable-area edge, so overflow never leaks into the pinned zone 指示器裁剪下界 = 可滚动区底边, 滚动时指示器溢出此处被裁, 不露进底部固定项区。
    indicatorClipBottom: topFlickable.y + topFlickable.height
    // Keep the indicator in lockstep with the item it marks 指示器与所标记的项锁步渐隐
    // A collapsed minimal pane shows no items, so it shows no indicator either
    // 极简模式折叠时没有条目, 也就不该有指示器
    indicatorOpacity: control.itemsVisible
        ? control._selectedItemFade : Enums.navigationFade.minOpacity

    // Forward signal 转发信号
    onCurrentItemChanged: (key) => currentItemUpdated(key)

    onPaneDisplayModeChanged: control._applyPaneDisplayMode()
    onEffectivePaneDisplayModeChanged: control._applyPaneDisplayMode()
    onIsPaneOpenChanged: control._applyPaneDisplayMode()
    Component.onCompleted: control._applyPaneDisplayMode()

    // ==================== Content 内容 ====================
    // Return button 返回按钮
    Rectangle {
        id: returnBtn

        readonly property int iconCenterMargin: (control.compactButtonWidth - Enums.iconSize.s) / 2
        // Touch has no hover preview: on touch the hover treatment follows the press
        // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
        readonly property bool _touchActive: Touch.feedback(returnArea.containsMouse, returnArea.pressed)

        visible: control.showReturnButton
        anchors.top: parent.top
        anchors.left: parent.left
        // Top margin includes title bar height to align with title text 顶部边距包含标题栏高度，与标题文字对齐
        anchors.topMargin: control.titleBarHeight + Enums.controlSize.navPanelPaddingV
        anchors.leftMargin: Enums.controlSize.navPanelPaddingH
        width: control.compactButtonWidth  // Always compact width 始终紧凑宽度
        height: Enums.controlSize.navItemHeight
        radius: Enums.radius.card
        color: returnBtn._touchActive ? Enums.stateColor.hover : Enums.transparent
        
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
        // Touch has no hover preview: on touch the hover treatment follows the press
        // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
        readonly property bool _touchActive: Touch.feedback(menuArea.containsMouse, menuArea.pressed)

        anchors.top: returnBtn.visible ? returnBtn.bottom : parent.top
        anchors.topMargin: returnBtn.visible ? Enums.controlSize.navItemSpacing : (control.titleBarHeight + Enums.controlSize.navPanelPaddingV)
        anchors.left: parent.left
        anchors.leftMargin: Enums.controlSize.navPanelPaddingH
        width: control.compactButtonWidth  // Always compact width 始终紧凑宽度
        height: Enums.controlSize.navItemHeight
        radius: Enums.radius.card
        color: menuBtn._touchActive ? Enums.stateColor.hover : Enums.transparent
        
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
            // In minimal mode the button opens the pane; in the other modes the same
            // gesture is the collapse/expand toggle.
            // 极简模式下这个按钮负责开合面板; 其它模式里同一个手势就是折叠/展开。
            onClicked: control.minimalPane ? control.togglePane() : control.toggle()
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

    // Passive hover, steals no delegate MouseArea events 被动悬停探测, 不抢委托的 MouseArea 事件
    HoverHandler { id: hostHover }

    // Top navigation items (scrollable) 顶部导航项（可滚动）
    // 上界接菜单按钮, 下界停在底部固定项之前; 没有这层 Flickable 时超出面板高度的
    // 项会被裁掉且无法触达。
    // Bounded between the menu button and the fixed bottom items; without this
    // Flickable, items past the panel height were clipped and unreachable.
    Flickable {
        id: topFlickable
        // A collapsed minimal pane hides its items and keeps only the menu button
        // 极简模式折叠时隐藏条目, 只留菜单按钮
        visible: control.itemsVisible
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
        // See the note in NavigationBar: no pressDelay needed.
        // 见 NavigationBar 同处注释: 无需 pressDelay。
        interactive: control.dragScrollEnabled

        Item {
            id: topLayout
            width: control.isCompact ? control.compactButtonWidth : topFlickable.width
            height: NavigationLayout.contentHeight(
                control._safeModel,
                Enums.controlSize.navItemHeight,
                Enums.controlSize.navItemSpacing)

            Repeater {
                id: topRep
                model: control._safeModel

                delegate: NavigationViewItem {
                    readonly property bool itemVisible: !modelData || modelData.visible !== false

                    visible: itemVisible
                    width: itemVisible ? parent.width : 0
                    // Explicit coordinates keep visible items contiguous around hidden entries.
                    // 显式坐标让隐藏项前后的可见项保持连续。
                    height: itemVisible ? implicitHeight : 0
                    y: NavigationLayout.itemY(
                        control._safeModel,
                        index,
                        Enums.controlSize.navItemHeight,
                        Enums.controlSize.navItemSpacing)
                    text: modelData ? (modelData.text || "") : ""
                    icon: modelData ? (modelData.icon || "") : ""
                    selected: itemVisible && index === control.currentIndex
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

    // Overlay rail as a sibling of topFlickable; inside, it would scroll away.
    // 浮层滚动轨: 与 topFlickable 同级, 不在其内部 —— 放进去会随内容一起滚动。
    NavigationScrollRail {
        objectName: "navigationViewScrollRail"
        flickable: topFlickable
        active: control.scrollRailEnabled
        // The hover-revealed rail stays revealed on touch 悬停显形的滚动轨在触摸端常显
        hostHovered: Touch.reveal(hostHover.hovered)
    }
    
    // Bottom fixed items 底部固定项
    Item {
        id: bottomLayout
        // Hidden together with the scrollable items in a collapsed minimal pane
        // 极简模式折叠时与可滚动条目一起隐藏
        visible: control.itemsVisible
        height: NavigationLayout.contentHeight(
            control._safeBottomItems,
            Enums.controlSize.navItemHeight,
            Enums.controlSize.navItemSpacing)
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.bottomMargin: Enums.controlSize.navPanelPaddingV
        anchors.leftMargin: Enums.controlSize.navPanelPaddingH
        width: control.isCompact ? control.compactButtonWidth : (parent.width - Enums.controlSize.navPanelPaddingH * 2)
        
        Repeater {
            id: bottomRep
            model: control._safeBottomItems

            delegate: NavigationViewItem {
                readonly property bool itemVisible: !modelData || modelData.visible !== false

                visible: itemVisible
                width: itemVisible ? parent.width : 0
                height: itemVisible ? implicitHeight : 0
                y: NavigationLayout.itemY(
                    control._safeBottomItems,
                    index,
                    Enums.controlSize.navItemHeight,
                    Enums.controlSize.navItemSpacing)
                text: modelData ? (modelData.text || "") : ""
                icon: modelData ? (modelData.icon || "") : ""
                // Bottom page items use key to find page index 底部页面项通过 key 查找页面索引来判断渲染状态
                selected: {
                    if (!itemVisible) return false
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
