// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../.."

// Layout - Unified layout component 统一布局组件
// Uses orient + flow properties to switch between different layout implementations 使用 orient + flow 属性切换不同的布局实现

// Orient 方向 (Enums.orient) - REQUIRED 必选参数:
//   flow (0): Flow layout (uses flow sub-enum) 流式布局（使用flow子枚举）
//   vertical (1): Vertical layout (VBoxLayout) 垂直布局
//   horizontal (2): Horizontal layout (HBoxLayout) 水平布局
//   grid (3): Grid layout 网格布局
//
// Flow 流式模式 (Enums.flow) - Only when orient=flow 仅当orient为flow时生效:
//   default_ (0): Compact packing 紧凑填充
//   vertical (1): Waterfall (equal width) 瀑布流（等宽）
//   horizontal (2): Equal height per row 同行等高
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    // REQUIRED: orient must be explicitly set 必选：orient必须显式设置
    property int orient: -1  // Invalid default, must be set 无效默认值，必须设置
    
    // Internal: track pending children to re-add after Loader reload 内部：跟踪重新加载待添加的子组件

    property var _pendingChildren: []
    
    // Trigger Loader reload when orient changes 当orient变化时触发Loader重新加载
    onOrientChanged: {
        if (orient >= 0 && orient <= 3 && loader.item) {
            // Save existing children before reload 重新加载前保存现有子组件
            var children = []
            var innerLayout = loader.item.childItems ? loader.item.childItems() : []
            for (var i = 0; i < innerLayout.length; i++) {
                var child = innerLayout[i]
                // Skip internal layout items (ColumnLayout/RowLayout)
                if (child.objectName !== "" || child.metaObject.className.indexOf("Layout") === -1) {
                    children.push(child)
                }
            }
            _pendingChildren = children
            
            loader.active = false
            loader.active = true
        }
    }
    property int flow: Enums.flow.default_  // Only for orient=flow 仅用于orient为flow时
    property int spacing: Enums.spacing.m
    property int rowSpacing: spacing  // For grid/flow 用于网格/流式
    property int columns: 2  // For grid mode 用于网格模式
    
    // Margins 边距
    property int margins: 0
    property int leftMargin: margins
    property int topMargin: margins
    property int rightMargin: margins
    property int bottomMargin: margins
    
    // Preferred size (set by Python, 0 means auto) 首选尺寸
    property real preferredWidth: 0
    property real preferredHeight: 0
    
    // Content container (for declarative children) 内容容器
    // Note: Cannot use alias to loader.item.content as Loader may not be ready; Python uses addWidget() while QML children set parent directly 注意：无法使用 alias 到 loader.item.content，因为 Loader 可能未就绪；Python 使用 addWidget()，QML 子项直接设置 parent
    
    // ==================== Size 尺寸 ====================
    // layoutFillHeight=false means use content height (for ScrollArea) layoutFillHeight=false 表示使用内容高度（用于 ScrollArea）
    property bool layoutFillWidth: true
    property bool layoutFillHeight: true
    
    // Width/Height: preferredSize > (fillXXX ? parent : implicit) 尺寸：preferredSize > (fillXXX ? 父容器 : implicit)
    width: preferredWidth > 0 ? preferredWidth : (Layout.fillWidth && parent ? parent.width : implicitWidth)
    height: preferredHeight > 0 ? preferredHeight : (Layout.fillHeight && parent ? parent.height : implicitHeight)
    implicitWidth: loader.item ? loader.item.implicitWidth : 0
    implicitHeight: loader.item ? loader.item.implicitHeight : 0
    
    // Padding aliases 内边距别名
    property int leftPadding: leftMargin
    property int rightPadding: rightMargin
    property int topPadding: topMargin
    property int bottomPadding: bottomMargin
    
    // Layout attached properties 布局附加属性
    Layout.fillWidth: true
    Layout.fillHeight: true
    
    // ==================== Validation 参数校验 ====================
    // Note: Validation moved to Loader only, Component.onCompleted fires too early for Python 注意：校验移至 Loader，Component.onCompleted 对 Python 来说太早

    // ==================== Qt-Style Layout Methods Qt风格布局方法 ====================
    function addWidget(widget, stretch) {
        if (loader.item && loader.item.addWidget) {
            loader.item.addWidget(widget, stretch)
        }
    }

    function insertWidget(index, widget) {
        if (loader.item && loader.item.insertWidget) {
            loader.item.insertWidget(index, widget)
        }
    }

    function removeWidget(widget) {
        if (loader.item && loader.item.removeWidget) {
            loader.item.removeWidget(widget)
        }
    }


    function setContentsMargins(left, top, right, bottom) {
        leftMargin = left
        topMargin = top
        rightMargin = right
        bottomMargin = bottom
    }

    function count() {
        if (loader.item && loader.item.count) {
            return loader.item.count()
        }
        return 0
    }

    function itemAt(index) {
        if (loader.item && loader.item.itemAt) {
            return loader.item.itemAt(index)
        }
        return null
    }

    function indexOf(widget) {
        if (loader.item && loader.item.indexOf) {
            return loader.item.indexOf(widget)
        }
        return -1
    }

    function isEmpty() {
        return count() === 0
    }

    function clear() {
        if (loader.item && loader.item.clear) {
            loader.item.clear()
        }
    }

    // ==================== Internal Loader 内部加载器 ====================
    Loader {
        id: loader
        objectName: "layoutLoader"
        anchors.fill: parent
        sourceComponent: {
            // Return null if orient not yet set (Python will set it and trigger reload) 如果 orient 未设置则返回 null（Python 会设置后触发重新加载）
            if (control.orient < 0 || control.orient > 3) {
                return null
            }
            
            switch (control.orient) {
                case Enums.orient.horizontal:
                    return hboxComponent
                case Enums.orient.grid:
                    return gridComponent
                case Enums.orient.flow:
                    return flowComponent
                case Enums.orient.vertical:
                    return vboxComponent
                default:
                    return null
            }
        }
        
        onLoaded: {
            // Sync properties to loaded layout 同步属性到加载的布局
            if (item) {
                if (item.spacing !== undefined) {
                    item.spacing = Qt.binding(function() { return control.spacing })
                }
                if (item.leftMargin !== undefined) {
                    item.leftMargin = Qt.binding(function() { return control.leftMargin })
                }
                if (item.topMargin !== undefined) {
                    item.topMargin = Qt.binding(function() { return control.topMargin })
                }
                if (item.rightMargin !== undefined) {
                    item.rightMargin = Qt.binding(function() { return control.rightMargin })
                }
                if (item.bottomMargin !== undefined) {
                    item.bottomMargin = Qt.binding(function() { return control.bottomMargin })
                }
                if (item.rowSpacing !== undefined) {
                    item.rowSpacing = Qt.binding(function() { return control.rowSpacing })
                }
                if (item.columns !== undefined) {
                    item.columns = Qt.binding(function() { return control.columns })
                }
                // Sync flow mode to FlowLayout 同步flow模式到FlowLayout
                if (item.mode !== undefined && control.orient === Enums.orient.flow) {
                    item.mode = Qt.binding(function() { return control.flow })
                }
                
                // Restore pending children after reload 重新加载后恢复子组件
                if (control._pendingChildren.length > 0) {
                    for (var i = 0; i < control._pendingChildren.length; i++) {
                        var child = control._pendingChildren[i]
                        if (child && item.addWidget) {
                            item.addWidget(child, 0)
                        }
                    }
                    control._pendingChildren = []
                }
            }
        }
    }
    
    // ==================== Layout Components 布局组件 ====================
    Component { id: vboxComponent; VBoxLayout { } }
    Component { id: hboxComponent; HBoxLayout { } }
    Component { id: gridComponent; GridLayout { columns: control.columns } }
    Component { id: flowComponent; FlowLayout { mode: control.flow } }
}
