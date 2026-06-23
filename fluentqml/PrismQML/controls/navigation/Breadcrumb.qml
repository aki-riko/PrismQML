// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal"

// BreadcrumbBar - Fluent Design breadcrumb navigation 面包屑导航栏
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int currentIndex: -1
    readonly property string currentKey: {
        if (_items.length > 0 && currentIndex >= 0 && currentIndex < _items.length) {
            return _items[currentIndex].key || ""
        }
        return ""
    }
    readonly property int count: _items.length
    property int maxVisibleItems: 5
    property bool showIcons: true
    property bool animated: true
    
    // ==================== Private Props 私有属性 ====================
    property var _items: []
    property var _itemMap: ({})
    property int _navDirection: 0
    property int _removeFromIndex: -1
    property int _newItemIndex: -1
    property var _newlyCollapsedIndices: []
    property var _newlyShownIndices: []
    property bool _shiftLeftActive: false
    property real _shiftLeftOffset: 0
    property real _shiftLeftTarget: 0
    property bool _shiftRightActive: false
    property real _shiftRightOffset: 0
    property real _shiftRightTarget: 0
    property bool _ellipsisWillHide: false
    
    // ==================== Signals 信号 ====================
    signal currentItemChanged(string key)
    
    // ==================== Size 尺寸 ====================
    // Ensure minimum width when empty for visibility 空状态时保证最小宽度以确保可见
    implicitWidth: Math.max(contentRow.implicitWidth, Enums.spacing.xxxl)
    implicitHeight: Enums.controlSize.inputHeightCompact
    clip: true
    
    // ==================== Computed Props 计算属性 ====================
    readonly property bool _hasOverflow: _items.length > maxVisibleItems
    readonly property var _collapsedItems: {
        if (!_hasOverflow) return []
        return _items.slice(1, _items.length - (maxVisibleItems - 2))
    }

    // ==================== Public Methods 公开方法 ====================
    function addItem(key, text, icon) {
        if (key in _itemMap) return
        _navDirection = 1
        _removeFromIndex = -1
        
        var newItems = _items.slice()
        newItems.push({ key: key, text: text, icon: icon || "" })
        var newLength = newItems.length
        var willOverflow = newLength > maxVisibleItems
        var newCollapsedIndices = []

        if (willOverflow) {
            var newCollapseEnd = newLength - (maxVisibleItems - 2)
            var oldCollapseEnd = _hasOverflow ? _items.length - (maxVisibleItems - 2) : 1
            for (var i = oldCollapseEnd; i < newCollapseEnd; i++) {
                if (i > 0 && i < newLength - (maxVisibleItems - 2)) {
                    newCollapsedIndices.push(i)
                }
            }
        }

        _newlyCollapsedIndices = newCollapsedIndices
        _itemMap[key] = newItems.length - 1
        _newItemIndex = newItems.length - 1
        _items = newItems
        currentIndex = newItems.length - 1
        currentItemChanged(key)

        if (newCollapsedIndices.length > 0 && animated) {
            var collapsedWidth = 0
            for (var k = 0; k < newCollapsedIndices.length; k++) {
                var collapsedIndex = newCollapsedIndices[k]
                var delegateItem = contentRepeater.itemAt(collapsedIndex)
                if (delegateItem) collapsedWidth += delegateItem.width
            }
            _shiftLeftTarget = -collapsedWidth
            _shiftLeftActive = true
            _shiftLeftOffset = 0
            shiftLeftAnim.restart()
            collapseToEllipsisTimer.restart()
        }
    }
    
    function setCurrentItem(key) {
        if (!(key in _itemMap)) return
        setCurrentIndex(_itemMap[key])
    }
    
    function setCurrentIndex(index) {
        if (index < 0 || index >= _items.length || index === currentIndex) return
        
        _navDirection = index < currentIndex ? -1 : 1
        _newItemIndex = -1
        _newlyShownIndices = []
        
        if (index < _items.length - 1) {
            _removeFromIndex = index + 1
            var newLength = index + 1
            var currentHasOverflow = _hasOverflow
            var newHasOverflow = newLength > maxVisibleItems
            var newShownIndices = []
            
            if (currentHasOverflow) {
                var currentCollapseEnd = _items.length - (maxVisibleItems - 2)
                var newCollapseEnd = newHasOverflow ? newLength - (maxVisibleItems - 2) : 1
                for (var i = newCollapseEnd; i < currentCollapseEnd; i++) {
                    if (i > 0 && i < newLength) newShownIndices.push(i)
                }
            }
            
            _newlyShownIndices = newShownIndices
            _ellipsisWillHide = currentHasOverflow && !newHasOverflow
            
            var removed = _items.slice(index + 1)
            for (var j = 0; j < removed.length; j++) {
                delete _itemMap[removed[j].key]
            }
            
            if (newShownIndices.length > 0 && animated) {
                var shownWidth = 0
                for (var k = 0; k < newShownIndices.length; k++) {
                    var shownIndex = newShownIndices[k]
                    var delegateItem = contentRepeater.itemAt(shownIndex)
                    if (delegateItem) shownWidth += delegateItem.width
                }
                _shiftRightTarget = shownWidth
                _shiftRightActive = true
                _shiftRightOffset = -shownWidth
                shiftRightAnim.restart()
                showFromEllipsisTimer.restart()
            }
            
            if (animated) removeTimer.restart()
            else _doRemove()
        }
        currentIndex = index
        currentItemChanged(_items[index].key)
    }
    
    function _doRemove() {
        if (_removeFromIndex > 0) {
            _items = _items.slice(0, _removeFromIndex)
            _removeFromIndex = -1
            _newlyShownIndices = []
            _shiftRightActive = false
            _shiftRightOffset = 0
            _ellipsisWillHide = false
        }
    }
    
    function item(key) {
        return (key in _itemMap) ? _items[_itemMap[key]] : null
    }
    
    function clear() {
        _navDirection = -1
        _removeFromIndex = 0
        _newItemIndex = -1
        for (var key in _itemMap) delete _itemMap[key]
        if (animated) removeTimer.restart()
        else _items = []
        currentIndex = -1
    }
    
    function popItem() {
        if (_items.length === 0) return
        if (_items.length >= 2) setCurrentIndex(currentIndex - 1)
        else clear()
    }
    
    // ==================== Public Methods 公共方法 ====================
    
    
    // Get count 获取项数
    function getCount() {
        return count
    }

    // ==================== Timers 定时器 ====================
    Timer {
        id: removeTimer
        interval: Enums.duration.crossFade
        onTriggered: control._doRemove()
    }
    
    Timer {
        id: collapseToEllipsisTimer
        interval: Enums.duration.dialog
        onTriggered: {
            control._newlyCollapsedIndices = []
            control._shiftLeftActive = false
            control._shiftLeftOffset = 0
        }
    }
    
    Timer {
        id: showFromEllipsisTimer
        interval: Enums.duration.crossFade
        onTriggered: {
            control._newlyShownIndices = []
            control._shiftRightActive = false
            control._shiftRightOffset = 0
            control._ellipsisWillHide = false
        }
    }
    
    // ==================== Animations 动画 ====================
    NumberAnimation {
        id: shiftLeftAnim
        target: control
        property: "_shiftLeftOffset"
        from: 0; to: control._shiftLeftTarget
        duration: Enums.duration.page
        easing.type: Easing.OutCubic
    }
    
    NumberAnimation {
        id: shiftRightAnim
        target: control
        property: "_shiftRightOffset"
        from: control._shiftRightOffset; to: 0
        duration: Enums.duration.page
        easing.type: Easing.OutCubic
    }
    
    // ==================== UI 界面 ====================
    Row {
        id: contentRow
        spacing: 0
        anchors.verticalCenter: parent.verticalCenter
        
        Repeater {
            id: contentRepeater
            model: _items
            
            delegate: BreadcrumbDelegate {}
        }
    }
}
