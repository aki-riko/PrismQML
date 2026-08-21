// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "_internal"

// NavigationBar - Fluent Design navigation bar (compact-nav window style) 导航栏
// Fixed width 72px, vertical layout (icon top, text bottom) 固定宽度垂直布局
// Extends NavigationPanelCore for common indicator/routing logic 继承NavigationPanelCore
NavigationPanelCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.navigationScroll
    property real scrollStep: Enums.spacing.navigationScrollStep
    // Fade items near an overflowing edge to hint the list scrolls 溢出端渐隐以提示可滚动
    property bool scrollFadeEnabled: true

    // ==================== Internal Props 内部属性 ====================
    // Maps key to page index for bottom page items 将 key 映射到页面索引，用于底部页面项
    property var _bottomPageIndexMap: ({})

    // ==================== Readonly State 只读状态 ====================
    // 选中项的渐隐值; 只在选中项属于可滚动区(顶部 repeater)时参与, 底部固定项不渐隐。
    readonly property real _selectedItemFade: scrollFade.selectionOpacity(
        control._getItemAt(control.currentIndex),
        control.currentIndex >= 0
            && control.currentIndex < (control._safeModel || []).length)

    // ==================== Public Methods 公开方法 ====================
    function smoothScrollTo(targetY) { topScrollBehavior.scrollTo(targetY) }
    function smoothScrollBy(delta) { topScrollBehavior.scrollBy(delta) }

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.navBarWidth
    implicitHeight: parent ? parent.height : 400
    
    // Indicator config 指示器配置
    indicatorX: Enums.spacing.xxs  // Edge position with minimal margin 边缘位置带最小间距
    indicatorWidth: Enums.controlSize.topNavIndicatorHeight
    indicatorHeight: Enums.controlSize.navIndicatorHeight
    backgroundColor: Enums.transparent
    borderEnabled: false  // compact-nav window style has no right border compact-nav window风格无右侧边框
    
    // Connect repeaters 连接 Repeater
    topRepeater: topRep
    bottomRepeater: bottomRep
    
    // Bind scroll offset for real-time indicator tracking 绑定滚动偏移以实时跟踪指示器
    scrollOffset: topFlickable.contentY
    // 指示器裁剪下界 = 可滚动区(topFlickable)底边, 滚动时指示器溢出此处被裁,
    // 不再露进底部固定项区(替代 Mica 下失效的 bottomCover 遮盖)。
    indicatorClipBottom: topFlickable.y + topFlickable.height
    // Keep the indicator in lockstep with the item it marks 指示器与所标记的项锁步渐隐
    indicatorOpacity: control._selectedItemFade

    // ==================== Content 内容 ====================
    // Edge fade state shared by the items and the indicator 导航项与指示器共用的渐隐状态
    NavigationScrollFade {
        id: scrollFade
        objectName: "navigationBarScrollFade"
        flickable: topFlickable
        active: control.scrollFadeEnabled
        itemHeight: Enums.controlSize.navBarItemHeight
        itemCount: topRep.count
    }

    // Top navigation items (scrollable) 顶部导航项（可滚动）
    Flickable {
        id: topFlickable
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: Enums.spacing.xs
        height: Math.max(0, parent.height - bottomLayout.height - Enums.spacing.xs * 2)
        
        contentWidth: width
        contentHeight: topLayout.height
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        interactive: false
        
        Column {
            id: topLayout
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: Enums.spacing.none
            
            Repeater {
                id: topRep
                model: control._safeModel
                
                delegate: NavigationBarItem {
                    text: modelData ? (modelData.text || "") : ""
                    icon: modelData ? (modelData.icon || "") : ""
                    selectedIcon: modelData ? (modelData.selectedIcon || "") : ""
                    selected: index === control.currentIndex
                    opacity: scrollFade.opacityAt(y, height)

                    onClicked: control._onItemClicked(index, false)
                }
            }
        }

        NavigationSmoothScroll {
            id: topScrollBehavior
            helperName: "navigationBarSmoothScrollHelper"
            flickable: topFlickable
            smoothScroll: control.smoothScroll
            duration: control.scrollDuration
            step: control.scrollStep
        }
    }
    
    // Bottom fixed items 底部固定项
    // 注: 原 bottomCover 遮盖矩形已移除 — 指示器现由 NavigationPanelCore 的
    // indicatorClip 裁剪容器按 indicatorClipBottom 裁掉溢出部分, 不再依赖颜色遮盖
    // (Mica 模式下遮盖矩形透明遮不住指示器)。
    Column {
        id: bottomLayout
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: Enums.spacing.xs
        spacing: Enums.spacing.none
        z: Enums.zIndex.controls + 1  // Above cover and indicator 高于遮盖层和指示器
        
        Repeater {
            id: bottomRep
            model: control._safeBottomItems
            
            delegate: NavigationBarItem {
                text: modelData ? (modelData.text || "") : ""
                icon: modelData ? (modelData.icon || "") : ""
                selectedIcon: modelData ? (modelData.selectedIcon || "") : ""
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
                selectable: !modelData || modelData.selectable !== false
                
                onClicked: {
                    // Always emit signal, let window handle page switch 始终发送信号，让窗口组件处理页面切换
                    control.bottomItemClicked(index)
                }
            }
        }
    }
}
