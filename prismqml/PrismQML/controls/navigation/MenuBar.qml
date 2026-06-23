// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../menus"
import "../buttons"
import "../data"

// MenuBar - Fluent Design menu bar 菜单栏
// Features: hover expand, smooth animation, custom Menu popup
// Refactored to use Button for stable hover 重构使用Button实现稳定hover
Rectangle {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    // Menu items data 菜单项数据
    // Format: [{text, children: [{text, icon, shortcut, action}, ...]}, ...]
    property var items: []
    
    // Active menu index (-1 = none) 当前激活菜单索引
    property int activeIndex: -1
    
    // Style props 样式属性
    property color backgroundColor: Enums.transparent
    property int itemPadding: Enums.spacing.l
    
    // ==================== Signals 信号 ====================
    signal menuItemClicked(string menuText, string itemText)
    signal _closeAllMenus()  // Internal signal to close all menus 内部信号关闭所有菜单
    
    // ==================== Size 尺寸 ====================
    implicitWidth: menuRow.implicitWidth
    implicitHeight: Enums.controlSize.inputHeight
    color: backgroundColor
    
    // ==================== Menu Items Row 菜单项行 ====================
    Row {
        id: menuRow
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.spacing.none
        
        Repeater {
            model: control.items
            
            // Menu item button 菜单项按钮
            Item {
                id: menuItemContainer
                width: menuBtn.implicitWidth
                height: Enums.controlSize.inputHeight
                
                property bool isActive: index === control.activeIndex
                
                // Hidden text for measuring 用于测量的隐藏文本
                Label {
                    id: menuBtnText
                    visible: false
                    type: Enums.label.type_caption
                    text: modelData.text || modelData
                }
                
                Button {
                    id: menuBtn
                    anchors.centerIn: parent
                    style: Enums.button.style_transparent
                    text: modelData.text || modelData
                    flat: true
                    
                    // Custom padding via implicitWidth 通过implicitWidth自定义padding
                    implicitWidth: menuBtnText.implicitWidth + control.itemPadding * 2
                    implicitHeight: Enums.controlSize.inputHeight
                    
                    onClicked: {
                        if (control.activeIndex === index) {
                            control.activeIndex = -1
                        } else {
                            control.activeIndex = index
                            _openMenuAt(index)
                        }
                    }
                    
                    onHoveredChanged: {
                        // Auto switch when another menu is open 另一菜单打开时自动切换
                        if (hovered && control.activeIndex >= 0 && control.activeIndex !== index) {
                            control.activeIndex = index
                            _openMenuAt(index)
                        }
                    }
                }
                
                // Open menu at this item 在此项打开菜单
                function _openMenuAt(idx) {
                    if (!modelData.children || modelData.children.length === 0) return
                    
                    // Close all other menus first 先关闭所有其他菜单
                    control._closeAllMenus()
                    
                    // Build menu dynamically 动态构建菜单
                    dropdownMenu.clear()
                    for (var i = 0; i < modelData.children.length; i++) {
                        var child = modelData.children[i]
                        if (child.separator) {
                            dropdownMenu.addSeparator()
                        } else {
                            var action = dropdownMenu.addAction(
                                child.text || child,
                                child.icon || "",
                                child.shortcut || ""
                            )
                        }
                    }
                    
                    // Open below this button 在按钮下方打开
                    dropdownMenu.openAtControl(menuBtn)
                }
                
                // Dropdown menu instance 下拉菜单实例
                Menu {
                    id: dropdownMenu
                    
                    // Listen for close all signal 监听关闭所有信号
                    Connections {
                        target: control
                        function on_CloseAllMenus() {
                            dropdownMenu.close()
                        }
                    }
                    
                    onActionTriggered: function(text) {
                        control.menuItemClicked(modelData.text, text)
                        control.activeIndex = -1
                    }
                    
                    onClosed: {
                        if (control.activeIndex === index) {
                            closeTimer.start()
                        }
                    }
                    
                    Timer {
                        id: closeTimer
                        interval: Enums.duration.fast
                        onTriggered: {
                            if (!menuBtn.hovered) {
                                control.activeIndex = -1
                            }
                        }
                    }
                }
            }
        }
    }
}
