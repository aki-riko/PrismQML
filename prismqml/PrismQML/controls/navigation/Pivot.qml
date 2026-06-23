// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../icons"
import "../buttons"
import "_internal"

// Pivot - Pivot navigation component 透视导航组件
// Refactored to use Button for stable hover 重构使用Button实现稳定hover
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var items: []
    property int currentIndex: 0
    property int indicatorSize: Enums.controlSize.navIndicatorHeight
    property int itemFontSize: Enums.typography.subtitle
    property int iconSize: Enums.iconSize.m
    property bool indicatorAnimmationEnabled: true
    
    // ==================== Signals 信号 ====================
    signal itemClicked(int index, bool byUser)
    signal currentItemChanged(string key)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: pivotRow.implicitWidth
    implicitHeight: Enums.controlSize.inputHeight
    
    // ==================== Internal 内部属性 ====================
    property int _prevIndex: -1
    property bool _initialized: false

    // ==================== Methods 方法 ====================
    function setCurrentIndex(idx) {
        if (idx < 0 || idx >= items.length) return
        if (idx === currentIndex && _initialized) return

        currentIndex = idx
        _updateIndicatorWithAnimation()

        var item = repeater.itemAt(idx)
        if (item) currentItemChanged(item.key)
    }

    function _getIndicatorX(item) {
        if (!item) return 0
        return item.x + (item.width - indicatorSize) / 2
    }

    // 构造指示器矩形 (底部细条)
    function _rectAt(item) {
        return Qt.rect(_getIndicatorX(item),
                       control.height - Enums.border.thick,
                       indicatorSize,
                       Enums.border.thick)
    }

    function _updateIndicatorWithAnimation() {
        var newItem = repeater.itemAt(currentIndex)
        if (!newItem) return

        var endRect = _rectAt(newItem)

        if (!_initialized) {
            navIndicator.setGeometry(endRect)
            _initialized = true
            _prevIndex = currentIndex
            return
        }

        if (!indicatorAnimmationEnabled || _prevIndex === currentIndex) {
            navIndicator.setGeometry(endRect)
            _prevIndex = currentIndex
            return
        }

        var prevItem = repeater.itemAt(_prevIndex)
        if (prevItem) {
            navIndicator.startAnimation(_rectAt(prevItem), endRect)
        } else {
            navIndicator.setGeometry(endRect)
        }

        _prevIndex = currentIndex
    }

    function setCurrentItem(key) {
        for (var i = 0; i < items.length; i++) {
            var item = repeater.itemAt(i)
            if (item && item.key === key) {
                setCurrentIndex(i)
                return
            }
        }
    }

    // ==================== Public Methods 公共方法 ====================


    // Add item 添加项目
    function addItem(key, text, icon) {
        var newItem = { key: key, text: text, icon: icon || "" }
        items = items.concat([newItem])
    }

    // Get current page key 获取当前页面键
    function getCurrentKey() {
        var item = repeater.itemAt(currentIndex)
        return item ? item.key : ""
    }

    // ==================== Items Row 项目行 ====================
    Row {
        id: pivotRow
        anchors.fill: parent
        spacing: Enums.spacing.none
        
        Repeater {
            id: repeater
            model: control.items
            
            Item {
                id: pivotItem
                width: pivotBtn.implicitWidth
                height: control.height
                
                property bool selected: index === control.currentIndex
                property string itemText: modelData.text !== undefined ? modelData.text : (typeof modelData === "string" ? modelData : "")
                property string itemIcon: modelData.icon !== undefined ? modelData.icon : ""
                property string key: modelData.key !== undefined ? modelData.key : (itemText !== "" ? itemText : itemIcon)
                property bool hasIcon: itemIcon !== ""
                property bool hasText: itemText !== ""
                
                Button {
                    id: pivotBtn
                    anchors.fill: parent
                    style: Enums.button.style_transparent
                    flat: true
                    text: pivotItem.itemText
                    icon: pivotItem.itemIcon
                    iconSize: control.iconSize
                    
                    onClicked: {
                        if (index !== control.currentIndex) {
                            control.setCurrentIndex(index)
                            control.itemClicked(index, true)
                        }
                    }
                }
            }
        }
    }
    
    // ==================== Indicator 指示器 (统一基类, 水平橡皮筋粘滞) ====================
    SlidingIndicator {
        id: navIndicator
        orientation: Qt.Horizontal
        indicatorWidth: control.indicatorSize
        indicatorHeight: Enums.border.thick
        radius: Enums.radius.micro
        animationEnabled: control.indicatorAnimmationEnabled
        visible: control.items.length > 0 && control._initialized
    }

    Component.onCompleted: Qt.callLater(_updateIndicatorWithAnimation)
    
    onWidthChanged: {
        if (_initialized && !navIndicator.running) {
            var item = repeater.itemAt(currentIndex)
            if (item) navIndicator.setGeometry(_rectAt(item))
        }
    }
}
