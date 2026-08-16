// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../menus"
import "../buttons"
import "../data"
import "_internal" as NavigationInternal

// MenuBar - Fluent Design menu bar 菜单栏
// Supports hover switching, smooth animation, and custom popups 支持悬停切换、平滑动画和自定义弹出菜单
// Uses Button to provide stable hover behavior 使用Button提供稳定的悬停行为
Rectangle {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    // Menu items data 菜单项数据
    // Format: [{text, children: [{text, icon, shortcut, action}, ...]}, ...] 格式见此对象数组
    property var items: []
    
    // Active menu index (-1 = none) 当前激活菜单索引
    property int activeIndex: -1
    
    // Style props 样式属性
    property color backgroundColor: Enums.transparent
    property int itemPadding: Enums.spacing.l

    // ==================== Readonly State 只读状态 ====================
    readonly property var _safeItems:
        items === null || items === undefined ? []
        : (typeof items.length === "number" ? items : [])
    
    // ==================== Signals 信号 ====================
    signal menuItemClicked(string menuText, string itemText)
    signal _closeAllMenus()  // Internal signal to close all menus 内部信号关闭所有菜单
    
    // ==================== Size 尺寸 ====================
    implicitWidth: menuRow.implicitWidth
    implicitHeight: Enums.controlSize.inputHeight
    color: backgroundColor
    
    // ==================== Content 内容 ====================
    Row {
        id: menuRow
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.spacing.none
        
        Repeater {
            model: control._safeItems
            
            // Menu item button 菜单项按钮
            Item {
                id: menuItemContainer

                property bool isActive: index === control.activeIndex
                property QtObject _closeTimer: null

                // Open menu at this item 在此项打开菜单
                function _openMenuAt(idx) {
                    if (!modelData || !modelData.children || modelData.children.length === 0) return

                    // Close all other menus first 先关闭所有其他菜单
                    control._closeAllMenus()

                    // Build menu dynamically 动态构建菜单
                    dropdownMenu.clear()
                    for (var i = 0; i < modelData.children.length; i++) {
                        var child = modelData.children[i]
                        if (!child) continue
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

                function _startCloseTimer() {
                    if (!_closeTimer) {
                        _closeTimer = closeTimerComponent.createObject(
                            menuItemContainer,
                            {
                                "menuButton": menuBtn,
                                "ownerItem": menuItemContainer
                            }
                        )
                    }
                    if (_closeTimer) _closeTimer.restart()
                }

                width: menuBtn.implicitWidth
                height: Enums.controlSize.inputHeight
                
                // Hidden text for measuring 用于测量的隐藏文本
                Label {
                    id: menuBtnText
                    visible: false
                    type: Enums.label.type_body
                    text: modelData ? (modelData.text || modelData) : ""
                }
                
                Button {
                    id: menuBtn
                    anchors.centerIn: parent
                    style: Enums.button.style_transparent
                    text: modelData ? (modelData.text || modelData) : ""
                    flat: true
                    contentAlignment: Enums.button.align_left
                    
                    // Custom padding via preferredWidth 通过preferredWidth自定义padding
                    preferredWidth: menuBtnText.implicitWidth + control.itemPadding * 2
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
                
                // Dropdown menu instance 下拉菜单实例
                Menu {
                    id: dropdownMenu

                    onActionTriggered: function(text) {
                        control.menuItemClicked(modelData ? (modelData.text || "") : "", text)
                        control.activeIndex = -1
                    }

                    onClosed: {
                        if (control.activeIndex === index) {
                            menuItemContainer._startCloseTimer()
                        }
                    }

                    // Listen for close all signal 监听关闭所有信号
                    Connections {
                        function on_CloseAllMenus() {
                            dropdownMenu.close()
                        }

                        target: control
                    }
                }
            }
        }
    }

    Component {
        id: closeTimerComponent

        NavigationInternal.MenuBarCloseTimer {
            menuBar: control
        }
    }
}
