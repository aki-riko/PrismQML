// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../icons"
import "../buttons"
import "_internal"

// Pivot - Pivot navigation component 透视导航组件
// Uses Button to provide stable hover behavior 使用Button提供稳定的悬停行为
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var items: []
    property int currentIndex: 0
    property int indicatorSize: Enums.controlSize.navIndicatorHeight
    property int itemFontSize: Enums.typography.subtitle
    property int iconSize: Enums.iconSize.m
    property bool indicatorAnimationEnabled: true

    // ==================== Internal Props 内部属性 ====================
    property int _prevIndex: -1
    property bool _initialized: false
    readonly property var _safeItems:
        items === null || items === undefined ? []
        : (typeof items.length === "number" ? items : [])
    
    // ==================== Signals 信号 ====================
    signal itemClicked(int index, bool byUser)
    signal currentItemChanged(string key)

    // ==================== Public Methods 公开方法 ====================
    function setCurrentIndex(idx) {
        if (idx < 0 || idx >= _safeItems.length) return
        if (idx === currentIndex && _initialized) return

        currentIndex = idx
        _updateIndicatorWithAnimation()

        var item = repeater.itemAt(idx)
        if (item) currentItemChanged(item.key)
    }

    // ==================== Internal Methods 内部方法 ====================
    function _getIndicatorX(item) {
        if (!item) return 0
        return item.x + (item.width - indicatorSize) / 2
    }

    // Build the bottom indicator rectangle 构造底部细条指示器矩形
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

        if (!indicatorAnimationEnabled || _prevIndex === currentIndex) {
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

    // ==================== Public Methods 公开方法 ====================
    function setCurrentItem(key) {
        for (var i = 0; i < _safeItems.length; i++) {
            var item = repeater.itemAt(i)
            if (item && item.key === key) {
                setCurrentIndex(i)
                return
            }
        }
    }

    // Add item 添加项目
    function addItem(key, text, icon) {
        var newItem = { key: key, text: text, icon: icon || "" }
        items = _safeItems.concat([newItem])
    }

    // Get current page key 获取当前页面键
    function getCurrentKey() {
        var item = repeater.itemAt(currentIndex)
        return item ? item.key : ""
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: pivotRow.implicitWidth
    implicitHeight: Enums.controlSize.inputHeight

    Component.onCompleted: Qt.callLater(_updateIndicatorWithAnimation)
    onWidthChanged: {
        if (_initialized && !navIndicator.running) {
            var item = repeater.itemAt(currentIndex)
            if (item) navIndicator.setGeometry(_rectAt(item))
        }
    }

    // ==================== Content 内容 ====================
    // Items row 项目行
    Row {
        id: pivotRow
        anchors.fill: parent
        spacing: Enums.spacing.none
        
        Repeater {
            id: repeater
            model: control._safeItems
            
            Item {
                id: pivotItem

                property bool selected: index === control.currentIndex
                property string itemText: typeof modelData === "string" ? modelData : (modelData && modelData.text !== undefined ? modelData.text : "")
                property string itemIcon: modelData && modelData.icon !== undefined ? modelData.icon : ""
                property string key: modelData && modelData.key !== undefined ? modelData.key : (itemText !== "" ? itemText : itemIcon)
                property bool hasIcon: itemIcon !== ""
                property bool hasText: itemText !== ""

                width: pivotBtn.implicitWidth
                height: control.height

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
    
    // Shared horizontal sticky-stretch indicator 统一基类的水平橡皮筋粘滞指示器
    SlidingIndicator {
        id: navIndicator
        orientation: Qt.Horizontal
        indicatorWidth: control.indicatorSize
        indicatorHeight: Enums.border.thick
        radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.micro
        animationEnabled: control.indicatorAnimationEnabled
        visible: control._safeItems.length > 0 && control._initialized
    }

}
