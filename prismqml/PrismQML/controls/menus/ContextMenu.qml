// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."

// ContextMenu - Context menu with auto-positioning 上下文菜单（自动定位）
// Usage 用法:
// Method 1: As child, auto-positions below parent 方式1：作为子元素，自动定位在父组件下方
// Method 2: Specify target control 方式2：指定目标控件
// Auto-bind right-click (autoBindRightClick: true) 右键自动绑定

MenuCore {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property bool autoBindRightClick: true  // Auto-bind right-click to parent 自动绑定右键
    property Item target: null              // Optional target control 可选目标控件
    
    // ==================== Internal 内部 ====================
    property Item _mouseArea: null
    
    Component.onCompleted: {
        if (parent && autoBindRightClick) {
            _mouseArea = mouseAreaComponent.createObject(parent)
        }
    }
    
    Component.onDestruction: {
        if (_mouseArea) {
            _mouseArea.destroy()
        }
    }
    
    // Watch for parent change 监听父组件变化
    onParentChanged: {
        if (parent && autoBindRightClick && !_mouseArea) {
            _mouseArea = mouseAreaComponent.createObject(parent)
        }
    }
    
    // ==================== Public Methods 公开方法 ====================
    // Bind right-click to parent (call after setParent) 绑定右键到父组件
    function bindToParent() {
        if (parent && autoBindRightClick) {
            if (_mouseArea) {
                _mouseArea.destroy()
            }
            _mouseArea = mouseAreaComponent.createObject(parent)
        }
    }
    
    // Show menu below target control 在目标控件下方显示菜单
    // @param targetItem: 可选，目标控件。不传则使用 target 属性或 parent
    function show(targetItem) {
        var ctrl = targetItem || target || parent
        if (ctrl) {
            openAtControl(ctrl)
        }
    }
    
    // ==================== Public Methods 公共方法 ====================
    
    
    // Hide menu (alias for close) 隐藏菜单（close别名）
    function hide() {
        close()
    }
    
    // Check if visible 检查是否可见
    function isVisible() {
        return popupVisible
    }
    
    // Execute action 执行菜单
    function exec(x, y, parentItem) {
        popup(x, y, parentItem || parent)
    }
    
    // MouseArea component for right-click 右键MouseArea组件
    Component {
        id: mouseAreaComponent
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.RightButton
            onClicked: (mouse) => {
                control.popup(mouse.x, mouse.y, parent)
            }
        }
    }
}
