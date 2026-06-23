// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../.."
import "ScrollBar"

// ScrollArea - Unified scroll area with virtualization support 统一滚动区域
// Control via type property: default/list/grid 通过type属性控制模式
// Usage 用法:
//   ScrollArea { content... }                           // Default 默认
//   ScrollArea { type: Enums.scroll.type_list; model: 1000; delegate: ... }  // List 列表
//   ScrollArea { type: Enums.scroll.type_grid; model: 1000; delegate: ... }  // Grid 网格
Item {
    id: control
    
    // ==================== Type 类型 ====================
    property int type: Enums.scroll.type_default
    
    // ==================== Common Props 通用属性 ====================
    property bool showScrollBar: true
    property int scrollBarWidth: 8
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    property int orientation: Qt.Horizontal | Qt.Vertical  // Scroll direction 滚动方向
    property int padding: Enums.spacing.xl  // Content padding 内容内边距
    
    // ==================== Default Mode Props 默认模式属性 ====================
    default property alias content: defaultLoader.content
    
    // ==================== Virtualized Mode Props 虚拟化模式属性 ====================
    property var model: []
    property Component delegate: null
    property int itemHeight: 40          // For list mode 列表模式
    property int cellWidth: 100          // For grid mode 网格模式
    property int cellHeight: 100         // For grid mode 网格模式
    property bool gridReuseItems: true   // Grid delegate 复用 (大数据网格滚动流畅的关键, 默认开)
    property int currentIndex: -1
    property bool selectable: true
    // List 模式额外属性 (向 ScrollAreaList 透传, 默认值不影响旧调用方)
    property int listSpacing: 0          // 列表项间距 (卡片化场景)
    property bool reuseItems: false      // delegate 复用, 大列表频繁 create/destroy 时打开
    property int listCacheBuffer: -1     // -1 = 引擎默认 itemHeight*10
    property bool delegateAsync: false   // 重 delegate 用 Loader.asynchronous 包一层防卡顿
    property bool alwaysShowScrollBar: false  // 滚动条常显
    property bool bounceEnabled: true    // 边界 bounce 回弹 (List 模式), false 防止顶/底空白闪烁
    
    // ==================== Expose Props 暴露属性 ====================
    readonly property real contentY: loader.item ? loader.item.contentY : 0
    readonly property real contentHeight: loader.item ? loader.item.contentHeight : 0
    readonly property int count: loader.item && loader.item.count !== undefined ? loader.item.count : 0
    
    // ==================== Signals 信号 ====================
    signal itemClicked(int index, var item)
    signal indexChanged(int index)
    
    // ==================== Size 尺寸 ====================
    // Preferred size (external override) 首选尺寸（外部覆盖）
    property real preferredWidth: 0
    property real preferredHeight: 0
    
    // Use implicit size for layout, actual size from parent binding 使用隐式尺寸用于布局，实际尺寸来自父容器绑定
    implicitWidth: preferredWidth > 0 ? preferredWidth : 200
    implicitHeight: preferredHeight > 0 ? preferredHeight : 200
    
    // Layout attached properties: allow filling parent layout 布局附加属性：允许填充父布局
    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.preferredWidth: preferredWidth > 0 ? preferredWidth : -1
    Layout.preferredHeight: preferredHeight > 0 ? preferredHeight : -1
    
    // ==================== Public Methods 公开方法 ====================
    function smoothScrollTo(targetY) { if (loader.item && loader.item.smoothScrollTo) loader.item.smoothScrollTo(targetY) }
    function smoothScrollBy(delta) { if (loader.item && loader.item.smoothScrollBy) loader.item.smoothScrollBy(delta) }
    function scrollToIndex(index) { if (loader.item && loader.item.scrollToIndex) loader.item.scrollToIndex(index) }
    function scrollToTop() { if (loader.item && loader.item.scrollToTop) loader.item.scrollToTop(); else smoothScrollTo(0) }
    function scrollToBottom() { if (loader.item && loader.item.scrollToBottom) loader.item.scrollToBottom() }
    
    // ==================== Public Methods 公共方法 ====================
    
    
    // Set cell size (for grid mode) 设置单元格尺寸（网格模式）
    function setCellSize(w, h) {
        cellWidth = w
        cellHeight = h
    }
    
    
    // ==================== Internal: Default content holder 内部：默认内容容器 ====================
    QtObject {
        id: defaultLoader
        default property list<QtObject> content
    }
    
    // ==================== Loader 动态加载器 ====================
    Loader {
        id: loader
        anchors.fill: parent
        sourceComponent: control.type === Enums.scroll.type_list ? listComponent :
                         control.type === Enums.scroll.type_grid ? gridComponent :
                         defaultComponent
    }
    
    // ==================== Default Component 默认组件 ====================
    Component {
        id: defaultComponent
        ScrollAreaDefault {
            showScrollBar: control.showScrollBar
            scrollBarWidth: control.scrollBarWidth
            smoothScroll: control.smoothScroll
            scrollDuration: control.scrollDuration
            scrollStep: control.scrollStep
            scrollEasing: control.scrollEasing
            orientation: control.orientation
            padding: control.padding
            content: defaultLoader.content
        }
    }
    
    // ==================== List Component 列表组件 ====================
    Component {
        id: listComponent
        ScrollAreaList {
            model: control.model
            delegate: control.delegate
            itemHeight: control.itemHeight
            spacing: control.listSpacing
            reuseItems: control.reuseItems
            cacheBuffer: control.listCacheBuffer
            delegateAsync: control.delegateAsync
            showScrollBar: control.showScrollBar
            alwaysShowScrollBar: control.alwaysShowScrollBar
            scrollBarWidth: control.scrollBarWidth
            smoothScroll: control.smoothScroll
            scrollDuration: control.scrollDuration
            scrollStep: control.scrollStep
            scrollEasing: control.scrollEasing
            bounceEnabled: control.bounceEnabled
            currentIndex: control.currentIndex
            selectable: control.selectable
            onItemClicked: (index, item) => control.itemClicked(index, item)
            onIndexChanged: (index) => control.indexChanged(index)
        }
    }
    
    // ==================== Grid Component 网格组件 ====================
    Component {
        id: gridComponent
        ScrollAreaGrid {
            model: control.model
            delegate: control.delegate
            cellWidth: control.cellWidth
            cellHeight: control.cellHeight
            reuseItems: control.gridReuseItems
            cacheBuffer: control.listCacheBuffer
            showScrollBar: control.showScrollBar
            scrollBarWidth: control.scrollBarWidth
            smoothScroll: control.smoothScroll
            scrollDuration: control.scrollDuration
            scrollStep: control.scrollStep
            scrollEasing: control.scrollEasing
            currentIndex: control.currentIndex
            selectable: control.selectable
            onItemClicked: (index, item) => control.itemClicked(index, item)
            onIndexChanged: (index) => control.indexChanged(index)
        }
    }
}
