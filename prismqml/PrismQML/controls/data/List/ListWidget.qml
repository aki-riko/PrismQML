// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import "../../../controls/containers/ScrollBar"
import "_internal/ListDataController.js" as ListDataController
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ListWidget - Fluent style list widget 列表控件
// QListWidget-style migration API subset QListWidget风格迁移接口子集
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Background 背景
    // cardColor overrides the default headerColor; use transparent for transparent scenes.
    // cardColor 可覆盖默认 headerColor；透明场景使用 cardColor:"transparent"。
    // Match the DataWidgetCore family API naming (ListView/TableView, etc.).
    // 与 DataWidgetCore 系列（ListView/TableView 等）API 命名一致。
    property color cardColor: Enums.headerColor
    property int borderRadius: Enums.radius.card

    // Selection mode 选择模式
    // QAbstractItemView.SelectionMode-style values QAbstractItemView选择模式风格取值
    readonly property int noSelection: 0
    readonly property int singleSelection: 1
    readonly property int multiSelection: 2
    readonly property int extendedSelection: 3
    readonly property int contiguousSelection: 4
    
    property int selectionMode: singleSelection
    
    property var model: []  // External model 外部模型
    readonly property int count: _externalModelLength > 0 ? _externalModelLength : listModel.count
    property alias currentIndex: listView.currentIndex
    property bool selectOnRightClick: false
    property bool showScrollBar: true
    property int scrollBarWidth: Enums.controlSize.scrollBarWidth
    property color checkedColor: Enums.accentColor
    property color checkedColorDark: Enums.accentColor
    property bool borderVisible: true
    
    // Smooth scroll props 平滑滚动属性
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    
    // Item delegate properties 列表项委托属性
    property Component itemDelegate: null

    // ==================== Internal Props 内部属性 ====================
    property int _hoverRow: -1
    property int _pressedRow: -1
    property var _selectedRows: []  // Multi-selection support 多选支持
    property var _previousItem: null
    property alias _listModel: listModel
    readonly property int _externalModelLength:
        model === null || model === undefined ? 0
        : (typeof model.length === "number" ? model.length : 0)
    readonly property alias _needsScrollBar: scrollViewportState.needsVertical
    readonly property alias _reserveScrollBarGutter:
        scrollViewportState.reserveVerticalGutter
    readonly property real _scrollBarGutter:
        Math.max(0, scrollBarWidth) + Enums.spacing.xs

    // ==================== Signals 信号 ====================
    signal itemClicked(int index, var item)
    signal itemDoubleClicked(int index, var item)
    signal itemPressed(int index, var item)
    signal itemEntered(int index, var item)
    signal currentItemChanged(var current, var previous)
    signal currentRowChanged(int currentRow)
    signal itemSelectionChanged()

    // ==================== Public Methods 公开方法 ====================
    // Item management 项管理

    // Add single item 添加单项
    function addItem(item) {
        ListDataController.addItem(control, item)
    }

    // Add multiple items 添加多项
    function addItems(items) {
        ListDataController.addItems(control, items)
    }

    // Insert item at row 在指定行插入项
    function insertItem(row, item) {
        ListDataController.insertItem(control, row, item)
    }

    // Insert multiple items 插入多项
    function insertItems(row, items) {
        ListDataController.insertItems(control, row, items)
    }

    // Take (remove and return) item at row 移除并返回指定行的项
    function takeItem(row) {
        return ListDataController.takeItem(control, row)
    }

    // Get item at row 获取指定行的项
    function item(row) {
        return ListDataController.item(control, row)
    }

    // Get row of item (by text match) 获取项的行号
    function row(item) {
        return ListDataController.row(control, item)
    }
    // Current item 当前项

    function currentItem() {
        return ListDataController.currentItem(control)
    }

    function setCurrentItem(item, command) {
        ListDataController.setCurrentItem(control, item, command)
    }

    function currentRow() {
        return ListDataController.currentRow(control)
    }

    function setCurrentRow(row, command) {
        ListDataController.setCurrentRow(control, row, command)
    }

    // Selection 选择

    function selectedItems() {
        return ListDataController.selectedItems(control)
    }

    function clearSelection() {
        ListDataController.clearSelection(control)
    }

    function selectAll() {
        ListDataController.selectAll(control)
    }

    function setSelectionMode(mode) {
        ListDataController.setSelectionMode(control, mode)
    }
    // Search 搜索

    // Find items matching text 查找匹配文本的项
    // flags: 0=ExactMatch, 1=Contains, 2=StartsWith, 3=EndsWith, 4=RegExp 匹配模式
    function findItems(text, flags) {
        return ListDataController.findItems(control, text, flags)
    }

    // Sorting 排序

    // Sort items (order: 0=Ascending, 1=Descending) 排序项目（0=升序，1=降序）
    function sortItems(order) {
        ListDataController.sortItems(control, order)
    }

    // Clear 清空

    function clear() {
        ListDataController.clear(control)
    }

    // Scroll 滚动

    function scrollToItem(item, hint) {
        var r = row(item)
        if (r >= 0) scrollToIndex(r)
    }

    function scrollToIndex(idx) {
        if (idx >= 0 && idx < listModel.count) {
            listView.positionViewAtIndex(idx, ListView.Center)
        }
    }

    function smoothScrollTo(targetY) {
        scrollHelper.scrollTo(targetY)
    }

    function smoothScrollBy(delta) {
        scrollHelper.scrollBy(delta)
    }
    // Item properties 项属性

    function setItemText(row, text) {
        ListDataController.setItemText(control, row, text)
    }

    function setItemIcon(row, icon) {
        ListDataController.setItemIcon(control, row, icon)
    }

    function setItemData(row, role, value) {
        ListDataController.setItemData(control, row, role, value)
    }

    function itemData(row, role) {
        return ListDataController.itemData(control, row, role)
    }

    function setItemCheckState(row, state) {
        ListDataController.setItemCheckState(control, row, state)
    }

    function itemCheckState(row) {
        return ListDataController.itemCheckState(control, row)
    }

    function setItemSelected(row, selected) {
        ListDataController.setItemSelected(control, row, selected)
    }

    function isItemSelected(row) {
        return _isRowSelected(row)
    }

    // ==================== Internal Methods 内部方法 ====================

    function _isRowSelected(row) {
        if (selectionMode === noSelection) return false
        if (selectionMode === singleSelection) return listView.currentIndex === row
        return _selectedRows.indexOf(row) >= 0
    }

    function _handleItemClick(row, button, modifiers) {
        ListDataController.handleItemClick(control, row, button, modifiers, Qt)
    }

    function _updateSelectedRows() {
        ListDataController.updateSelectedRows(control)
    }

    // ==================== Internal Methods 内部方法 ====================
    function _scheduleScrollBarUpdate() {
        if (scrollViewportState) scrollViewportState.invalidate()
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.listDefaultWidth
    implicitHeight: Enums.controlSize.listDefaultHeight
    color: cardColor
    radius: borderRadius
    onWidthChanged: _scheduleScrollBarUpdate()
    onHeightChanged: _scheduleScrollBarUpdate()
    onScrollBarWidthChanged: _scheduleScrollBarUpdate()

    // ==================== Content 内容 ====================
    // Internal model 内部模型
    ListModel { id: listModel }

    // List view 列表视图
    ListView {
        id: listView
        objectName: "listWidgetViewport"
        anchors.fill: parent
        anchors.rightMargin: control._reserveScrollBarGutter
            ? Math.min(control._scrollBarGutter, Math.max(0, parent.width)) : 0
        clip: true
        boundsBehavior: Flickable.DragAndOvershootBounds
        interactive: false
        // Performance: reuse delegates and prerender offscreen boundaries. 性能：复用委托并预渲染屏外边界。
        reuseItems: true
        cacheBuffer: 600
        model: control._externalModelLength > 0 ? control.model : listModel
        
        // Padding 内边距
        leftMargin: Enums.spacing.xs
        rightMargin: Enums.spacing.xs
        
        // Default delegate 默认委托
        delegate: control.itemDelegate ? control.itemDelegate : defaultDelegate
        
        // Selection changed 选中变化
        onCurrentIndexChanged: {
            var currentItem = control.item(currentIndex)
            control.currentItemChanged(currentItem, control._previousItem)
            control.currentRowChanged(currentIndex)
            control._previousItem = currentItem
        }
    }

    ScrollViewportState {
        id: scrollViewportState
        target: listView
        scrollBarsEnabled: control.showScrollBar
        verticalEnabled: true
        itemCount: listView.count
    }
    
    // Smooth scroll helper 平滑滚动助手
    SmoothScrollHelper {
        id: scrollHelper
        target: listView
        orientation: Qt.Vertical
        enabled: control.smoothScroll
        duration: control.scrollDuration
        step: control.scrollStep
        easing: control.scrollEasing
        bounceEnabled: true
        handleWheel: true
    }
    
    // Scrollbar 滚动条
    ScrollBar {
        id: scrollBar
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: Enums.spacing.xxs
        
        target: listView
        scrollHelper: scrollHelper
        orientation: Qt.Vertical
        barWidth: Math.max(0, scrollBarWidth)
        visible: control._needsScrollBar
    }

    // Default delegate 默认委托
    Component {
        id: defaultDelegate
        
        ListWidgetItem {
            id: delegateItem
            required property int index
            required property var modelData
            
            // Normalize modelData 规范化数据
            property string _text: typeof modelData === "string" ? modelData : (modelData ? (modelData.text || "") : "")
            property string _icon: typeof modelData === "string" ? "" : (modelData ? (modelData.icon || "") : "")
            
            width: listView.width - listView.leftMargin - listView.rightMargin
            itemIndex: delegateItem.index
            itemData: ({ text: _text, icon: _icon, data: {} })
            hovered: control._hoverRow === delegateItem.index
            pressed: control._pressedRow === delegateItem.index
            selected: control._isRowSelected(delegateItem.index)
            
            onClicked: {
                control._handleItemClick(delegateItem.index, Qt.LeftButton, Qt.NoModifier)
                control.itemClicked(delegateItem.index, { text: _text, icon: _icon, row: delegateItem.index })
            }
            onDoubleClicked: control.itemDoubleClicked(delegateItem.index, { text: _text, icon: _icon, row: delegateItem.index })
            onHoveredChanged: {
                if (hovered) {
                    control._hoverRow = delegateItem.index
                    control.itemEntered(delegateItem.index, { text: _text, icon: _icon, row: delegateItem.index })
                } else if (control._hoverRow === delegateItem.index) {
                    control._hoverRow = -1
                }
            }
            onPressedChanged: {
                if (pressed) {
                    control._pressedRow = delegateItem.index
                    control.itemPressed(delegateItem.index, { text: _text, icon: _icon, row: delegateItem.index })
                }
            }
        }
    }
    
    // Hover tracking 悬停跟踪
    MouseArea {
        anchors.fill: listView
        acceptedButtons: Qt.NoButton
        hoverEnabled: true
        z: Enums.zIndex.background
        onExited: control._hoverRow = -1
    }

}
