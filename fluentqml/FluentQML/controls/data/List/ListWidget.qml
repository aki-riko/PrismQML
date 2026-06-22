// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../../.."
import "../../../controls/containers/ScrollBar"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ListWidget - Fluent style list widget 列表控件
// QListWidget-style migration API subset QListWidget风格迁移接口子集
Rectangle {
    id: control
    
    // ==================== Background 背景 ====================
    // cardColor 可覆盖(默认主题 headerColor): 透明场景设 cardColor:"transparent",
    // 与 DataWidgetCore 系列(ListView/TableView 等)API 命名一致。
    property color cardColor: Enums.headerColor
    color: cardColor
    radius: Enums.radius.card
    
    // ==================== Selection Mode 选择模式 ====================
    // QAbstractItemView.SelectionMode-style values QAbstractItemView选择模式风格取值
    readonly property int noSelection: 0
    readonly property int singleSelection: 1
    readonly property int multiSelection: 2
    readonly property int extendedSelection: 3
    readonly property int contiguousSelection: 4
    
    property int selectionMode: singleSelection
    
    // ==================== Public Props 公开属性 ====================
    property var model: []  // External model 外部模型
    readonly property int count: model.length > 0 ? model.length : listModel.count
    property alias currentIndex: listView.currentIndex
    property bool selectOnRightClick: false
    property bool showScrollBar: true
    property int scrollBarWidth: Enums.controlSize.scrollBarWidth
    property color checkedColor: Enums.accentColor
    property color checkedColorDark: Enums.accentColor
    property bool borderVisible: true
    property int borderRadius: Enums.radius.card
    
    // Smooth scroll props 平滑滚动属性
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    
    // Item delegate properties 列表项委托属性
    property Component itemDelegate: null
    
    // ==================== Signals 信号 ====================
    signal itemClicked(int index, var item)
    signal itemDoubleClicked(int index, var item)
    signal itemPressed(int index, var item)
    signal itemEntered(int index, var item)
    signal currentItemChanged(var current, var previous)
    signal currentRowChanged(int currentRow)
    signal itemSelectionChanged()
    
    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.listDefaultWidth
    implicitHeight: Enums.controlSize.listDefaultHeight
    
    // ==================== Internal State 内部状态 ====================
    property int _hoverRow: -1
    property int _pressedRow: -1
    property var _selectedRows: []  // Multi-selection support 多选支持
    property var _previousItem: null

    // ==================== Selection Helper 选择辅助 ====================
    function _isRowSelected(row) {
        if (selectionMode === noSelection) return false
        if (selectionMode === singleSelection) return listView.currentIndex === row
        return _selectedRows.indexOf(row) >= 0
    }

    function _handleItemClick(row, button, modifiers) {
        if (selectionMode === noSelection) return

        if (button === Qt.RightButton && !selectOnRightClick) return

        if (selectionMode === singleSelection) {
            listView.currentIndex = row
            _selectedRows = [row]
        } else if (selectionMode === multiSelection) {
            var idx = _selectedRows.indexOf(row)
            if (idx >= 0) {
                _selectedRows.splice(idx, 1)
            } else {
                _selectedRows.push(row)
            }
            _selectedRows = _selectedRows.slice()  // Trigger binding update
            listView.currentIndex = row
        } else if (selectionMode === extendedSelection) {
            if (modifiers & Qt.ControlModifier) {
                var idx2 = _selectedRows.indexOf(row)
                if (idx2 >= 0) _selectedRows.splice(idx2, 1)
                else _selectedRows.push(row)
                _selectedRows = _selectedRows.slice()
            } else if (modifiers & Qt.ShiftModifier && listView.currentIndex >= 0) {
                var start = Math.min(listView.currentIndex, row)
                var end = Math.max(listView.currentIndex, row)
                _selectedRows = []
                for (var i = start; i <= end; i++) _selectedRows.push(i)
            } else {
                _selectedRows = [row]
            }
            listView.currentIndex = row
        }
        _pressedRow = -1
        itemSelectionChanged()
    }

    function _updateSelectedRows() {
        // Called when model changes 模型变化时调用
        _selectedRows = _selectedRows.filter(function(r) { return r < listModel.count })
    }
    // ==================== QListWidget API - Item Management 项管理 ====================

    // Add single item 添加单项
    function addItem(item) {
        var entry = _normalizeItem(item)
        listModel.append(entry)
    }

    // Add multiple items 添加多项
    function addItems(items) {
        for (var i = 0; i < items.length; i++) {
            addItem(items[i])
        }
    }

    // Insert item at row 在指定行插入项
    function insertItem(row, item) {
        if (row < 0) row = 0
        if (row > listModel.count) row = listModel.count
        var entry = _normalizeItem(item)
        listModel.insert(row, entry)
    }

    // Insert multiple items 插入多项
    function insertItems(row, items) {
        for (var i = 0; i < items.length; i++) {
            insertItem(row + i, items[i])
        }
    }

    // Take (remove and return) item at row 移除并返回指定行的项
    function takeItem(row) {
        if (row < 0 || row >= listModel.count) return null
        var item = _getItemObject(row)
        listModel.remove(row)
        _updateSelectedRows()
        return item
    }

    // Get item at row 获取指定行的项
    function item(row) {
        if (row < 0 || row >= listModel.count) return null
        return _getItemObject(row)
    }

    // Get row of item (by text match) 获取项的行号
    function row(item) {
        var searchText = typeof item === "string" ? item : (item.text || "")
        for (var i = 0; i < listModel.count; i++) {
            if (listModel.get(i).text === searchText) return i
        }
        return -1
    }
    // ==================== QListWidget API - Current Item 当前项 ====================

    function currentItem() {
        return item(listView.currentIndex)
    }

    function setCurrentItem(item, command) {
        var r = row(item)
        if (r >= 0) setCurrentRow(r, command)
    }

    function currentRow() {
        return listView.currentIndex
    }

    function setCurrentRow(row, command) {
        if (row >= 0 && row < listModel.count) {
            listView.currentIndex = row
            if (selectionMode !== noSelection) {
                _selectedRows = [row]
                itemSelectionChanged()
            }
        }
    }

    // ==================== QListWidget API - Selection 选择 ====================

    function selectedItems() {
        var result = []
        for (var i = 0; i < _selectedRows.length; i++) {
            var it = item(_selectedRows[i])
            if (it) result.push(it)
        }
        return result
    }

    function clearSelection() {
        _selectedRows = []
        listView.currentIndex = -1
        itemSelectionChanged()
    }

    function selectAll() {
        if (selectionMode === noSelection || selectionMode === singleSelection) return
        _selectedRows = []
        for (var i = 0; i < listModel.count; i++) {
            _selectedRows.push(i)
        }
        itemSelectionChanged()
    }

    function setSelectionMode(mode) {
        selectionMode = mode
        if (mode === singleSelection && _selectedRows.length > 1) {
            _selectedRows = listView.currentIndex >= 0 ? [listView.currentIndex] : []
        }
    }
    // ==================== QListWidget API - Search 搜索 ====================

    // Find items matching text 查找匹配文本的项
    // flags: 0=ExactMatch, 1=Contains, 2=StartsWith, 3=EndsWith, 4=RegExp
    function findItems(text, flags) {
        var result = []
        var pattern = text.toLowerCase()
        for (var i = 0; i < listModel.count; i++) {
            var itemText = (listModel.get(i).text || "").toLowerCase()
            var match = false
            if (flags === 0) match = (itemText === pattern)
            else if (flags === 1) match = (itemText.indexOf(pattern) >= 0)
            else if (flags === 2) match = itemText.startsWith(pattern)
            else if (flags === 3) match = itemText.endsWith(pattern)
            else if (flags === 4) match = new RegExp(text).test(itemText)
            if (match) result.push(_getItemObject(i))
        }
        return result
    }

    // ==================== QListWidget API - Sorting 排序 ====================

    // Sort items (order: 0=Ascending, 1=Descending)
    function sortItems(order) {
        var items = []
        for (var i = 0; i < listModel.count; i++) {
            items.push(listModel.get(i))
        }
        items.sort(function(a, b) {
            var cmp = (a.text || "").localeCompare(b.text || "")
            return order === 1 ? -cmp : cmp
        })
        listModel.clear()
        for (var j = 0; j < items.length; j++) {
            listModel.append(items[j])
        }
    }

    // ==================== QListWidget API - Clear 清空 ====================

    function clear() {
        listModel.clear()
        _selectedRows = []
        listView.currentIndex = -1
    }

    // ==================== QListWidget API - Scroll 滚动 ====================

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
    // ==================== QListWidget API - Border 边框 ====================


    // ==================== QListWidget API - Item Properties 项属性 ====================

    function setItemText(row, text) {
        if (row >= 0 && row < listModel.count) {
            listModel.setProperty(row, "text", text)
        }
    }

    function setItemIcon(row, icon) {
        if (row >= 0 && row < listModel.count) {
            listModel.setProperty(row, "icon", icon)
        }
    }

    function setItemData(row, role, value) {
        if (row >= 0 && row < listModel.count) {
            var d = listModel.get(row).data || {}
            d[role] = value
            listModel.setProperty(row, "data", d)
        }
    }

    function itemData(row, role) {
        if (row < 0 || row >= listModel.count) return undefined
        var d = listModel.get(row).data
        return d ? d[role] : undefined
    }

    function setItemCheckState(row, state) {
        if (row >= 0 && row < listModel.count) {
            listModel.setProperty(row, "checkState", state)
        }
    }

    function itemCheckState(row) {
        if (row < 0 || row >= listModel.count) return 0
        return listModel.get(row).checkState || 0
    }

    function setItemSelected(row, selected) {
        if (row < 0 || row >= listModel.count) return
        listModel.setProperty(row, "selected", selected)
        var idx = _selectedRows.indexOf(row)
        if (selected && idx < 0) {
            _selectedRows.push(row)
        } else if (!selected && idx >= 0) {
            _selectedRows.splice(idx, 1)
        }
        _selectedRows = _selectedRows.slice()
    }

    function isItemSelected(row) {
        return _isRowSelected(row)
    }

    // ==================== Internal Helpers 内部辅助 ====================

    function _normalizeItem(item) {
        if (typeof item === "string") {
            return { text: item, icon: "", data: {}, checkable: false, checkState: 0, selected: false, flags: 0 }
        }
        return {
            text: item.text || "",
            icon: item.icon || item.iconSource || "",
            data: item.data || {},
            checkable: item.checkable || false,
            checkState: item.checkState || item.checked || 0,
            selected: item.selected || false,
            flags: item.flags || 0
        }
    }

    function _getItemObject(row) {
        if (row < 0 || row >= listModel.count) return null
        var m = listModel.get(row)
        return {
            text: m.text,
            icon: m.icon,
            data: m.data,
            checkable: m.checkable,
            checkState: m.checkState,
            selected: _isRowSelected(row),
            row: row
        }
    }

    // ==================== Internal Model 内部模型 ====================
    ListModel { id: listModel }
    
    // ==================== ListView 列表视图 ====================
    ListView {
        id: listView
        anchors.fill: parent
        anchors.rightMargin: showScrollBar && contentHeight > height ? scrollBarWidth + Enums.spacing.xs : 0
        clip: true
        boundsBehavior: Flickable.DragAndOvershootBounds
        interactive: false
        // 性能: reuseItems 复用 delegate, cacheBuffer 屏外预渲染避免边界卡顿
        reuseItems: true
        cacheBuffer: 600
        model: control.model.length > 0 ? control.model : listModel
        
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
    
    // ==================== Smooth Scroll Helper 平滑滚动助手 ====================
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
    
    // ==================== Scrollbar 滚动条 ====================
    ScrollBar {
        id: scrollBar
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: Enums.spacing.xxs
        
        target: listView
        scrollHelper: scrollHelper
        orientation: Qt.Vertical
        barWidth: scrollBarWidth
        visible: showScrollBar && listView.contentHeight > listView.height
    }

    // ==================== Default Delegate 默认委托 ====================
    Component {
        id: defaultDelegate
        
        ListWidgetItem {
            id: delegateItem
            required property int index
            required property var modelData
            
            // Normalize modelData 规范化数据
            property string _text: typeof modelData === "string" ? modelData : (modelData.text || "")
            property string _icon: typeof modelData === "string" ? "" : (modelData.icon || "")
            
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
    
    // ==================== Hover Tracking 悬停跟踪 ====================
    MouseArea {
        anchors.fill: listView
        acceptedButtons: Qt.NoButton
        hoverEnabled: true
        z: Enums.zIndex.background
        onExited: control._hoverRow = -1
    }

}
