// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import ".."

// NavigationBar - Fluent Design navigation bar (compact-nav window style) 导航栏
// Fixed width 72px, vertical layout (icon top, text bottom) 固定宽度垂直布局
// Extends NavigationPanelCore for common indicator/routing logic 继承NavigationPanelCore
NavigationPanelCore {
    id: control
    
    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.navBarWidth
    implicitHeight: parent ? parent.height : 400
    
    // ==================== Indicator Config 指示器配置 ====================
    indicatorX: Enums.spacing.xxs  // Edge position with minimal margin 边缘位置带最小间距
    indicatorWidth: Enums.controlSize.topNavIndicatorHeight
    indicatorHeight: Enums.controlSize.navIndicatorHeight
    backgroundColor: Enums.transparent
    borderEnabled: false  // compact-nav window style has no right border compact-nav window风格无右侧边框
    
    // ==================== Connect Repeaters 连接Repeater ====================
    topRepeater: topRep
    bottomRepeater: bottomRep
    
    // ==================== Bottom Page Index Map 底部页面索引映射 ====================
    // Maps key to page index for bottom page items 将 key 映射到页面索引，用于底部页面项
    property var _bottomPageIndexMap: ({})
    
    // Bind scroll offset for real-time indicator tracking 绑定滚动偏移以实时跟踪指示器
    scrollOffset: topFlickable.contentY
    // 指示器裁剪下界 = 可滚动区(topFlickable)底边, 滚动时指示器溢出此处被裁,
    // 不再露进底部固定项区(替代 Mica 下失效的 bottomCover 遮盖)。
    indicatorClipBottom: topFlickable.y + topFlickable.height
    
    // ==================== Top Nav Items (Scrollable) 顶部导航项 ====================
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
        interactive: contentHeight > height
        
        Column {
            id: topLayout
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: Enums.spacing.none
            
            Repeater {
                id: topRep
                model: control.model
                
                delegate: NavigationBarItem {
                    text: modelData.text || ""
                    icon: modelData.icon || ""
                    selectedIcon: modelData.selectedIcon || ""
                    selected: index === control.currentIndex
                    
                    onClicked: control._onItemClicked(index, false)
                }
            }
        }
    }
    
    // ==================== Bottom Fixed Items 底部固定项 ====================
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
            model: control.bottomItems
            
            delegate: NavigationBarItem {
                text: modelData.text || ""
                icon: modelData.icon || ""
                selectedIcon: modelData.selectedIcon || ""
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
                selectable: modelData.selectable !== false
                
                onClicked: {
                    // Always emit signal, let window handle page switch 始终发送信号，让窗口组件处理页面切换
                    control.bottomItemClicked(index)
                }
            }
        }
    }
}
