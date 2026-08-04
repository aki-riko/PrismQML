// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../.."
import "../icons"
import "../data"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// CycleWheelPicker - Cycle wheel picker with scroll buttons 循环滚轮选择器（带滚动按钮）
// A Fluent Design style scrollable wheel selector Fluent Design 风格的循环滚轮选择器
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var items: []  // Options list 选项列表
    property int currentIndex: 0
    property string currentValue: (items && items.length > 0) ? String(items[currentIndex]) : ""
    property int itemHeight: Enums.controlSize.wheelPickerRowHeight  // Row height 行高
    property int visibleItems: 9  // Visible row count (odd, centered selection) 可见行数(奇数,居中选中)
    property bool showScrollButtons: true  // Show scroll buttons on hover 悬停时显示滚动按钮
    property int textAlignment: Text.AlignHCenter  // Text alignment 文本对齐
    property bool cycle: true  // Enable infinite scroll 启用无限滚动

    // ==================== Internal Props 内部属性 ====================
    property bool _hovered: false
    property bool _repeatStarted: false
    property int _repeatDirection: 0
    readonly property var _safeItems: _listOrEmpty(items)
    readonly property int _safeItemHeight: Math.max(1, itemHeight)
    readonly property int _safeVisibleItems: Math.max(1, visibleItems)
    readonly property int _safeCurrentIndex: _safeItems.length > 0
        ? Math.max(0, Math.min(currentIndex, _safeItems.length - 1)) : 0

    // ==================== Signals 信号 ====================
    signal currentItemChanged(int index, string value)

    // ==================== Public Methods 公开方法 ====================
    function scrollUp() {
        if (_safeItems.length === 0) return
        if (cycle) {
            pathView.decrementCurrentIndex()
        } else {
            if (listView.currentIndex > 0) listView.currentIndex--
        }
    }

    function scrollDown() {
        if (_safeItems.length === 0) return
        if (cycle) {
            pathView.incrementCurrentIndex()
        } else {
            if (listView.currentIndex < _safeItems.length - 1) listView.currentIndex++
        }
    }

    function setCurrentIndex(index) {
        if (index >= 0 && index < _safeItems.length) {
            currentIndex = index
            if (cycle) {
                pathView.currentIndex = index
            } else {
                listView.currentIndex = index
                listView.positionViewAtIndex(index, ListView.Center)
            }
        }
    }

    function setCurrentValue(value) {
        var strValue = String(value)
        for (var i = 0; i < _safeItems.length; i++) {
            if (String(_safeItems[i]) === strValue) {
                setCurrentIndex(i)
                return
            }
        }
    }

    // Get current index 获取当前索引
    function getCurrentIndex() { return currentIndex }

    // Get current item 获取当前选项
    function currentItem() { return currentValue }

    // ==================== Internal Methods 内部方法 ====================
    function _listOrEmpty(value) {
        return value && typeof value.length === "number" ? value : []
    }

    function _distanceFromCenter(center, itemCenter) {
        var span = control.height / 2
        return span > 0 && isFinite(span) ? Math.abs(center - itemCenter) / span : 0
    }

    function _startRepeat(direction) {
        _repeatDirection = direction < 0 ? -1 : 1
        _repeatStarted = false
        repeatTimer.restart()
    }

    function _stopRepeat(direction) {
        if (_repeatDirection !== direction) return
        repeatTimer.stop()
        _repeatDirection = 0
        _repeatStarted = false
    }

    function _triggerRepeat() {
        if (_repeatDirection < 0) scrollUp()
        else if (_repeatDirection > 0) scrollDown()
        else {
            repeatTimer.stop()
            return
        }
        _repeatStarted = true
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: 80
    implicitHeight: _safeItemHeight * _safeVisibleItems

    // Sync view index when items change 当items变化时同步视图索引
    onItemsChanged: {
        if (_safeItems.length > 0 && currentIndex !== _safeCurrentIndex) {
            currentIndex = _safeCurrentIndex
        }
        Qt.callLater(function() {
            if (_safeItems.length === 0) return
            if (cycle) {
                pathView.currentIndex = _safeCurrentIndex
            } else {
                listView.currentIndex = _safeCurrentIndex
            }
        })
    }

    // ==================== Content 内容 ====================
    // Cyclic scrolling path view 循环滚动 PathView
    PathView {
        id: pathView
        anchors.fill: parent
        visible: control.cycle
        model: control.cycle ? control._safeItems : []
        pathItemCount: control._safeVisibleItems + 2
        preferredHighlightBegin: 0.5
        preferredHighlightEnd: 0.5
        highlightRangeMode: PathView.StrictlyEnforceRange
        snapMode: PathView.SnapToItem
        clip: true
        interactive: true
        
        currentIndex: control._safeCurrentIndex
        onCurrentIndexChanged: {
            if (control.cycle && control.currentIndex !== currentIndex) {
                control.currentIndex = currentIndex
                control.currentItemChanged(currentIndex, control.currentValue)
            }
        }
        
        path: Path {
            startX: control.width / 2
            startY: -control.itemHeight
            PathLine {
                x: control.width / 2
                y: control.height + control.itemHeight
            }
        }
        
        delegate: Item {
            property real distanceFromCenter: {
                var center = control.height / 2
                var itemCenter = y + height / 2
                return control._distanceFromCenter(center, itemCenter)
            }

            width: control.width
            height: control._safeItemHeight
            x: -width / 2  // PathView centers on path, offset to fill width 沿路径居中,左偏使内容填满列
            // Keep Item instead of Rectangle so transparent delegates do not occlude the popup highlight.
            // 保持 Item，避免透明 Rectangle 委托遮挡弹窗选中高亮。

            Label {
                anchors.centerIn: parent
                type: Enums.label.type_body
                text: String(modelData)
                font.pixelSize: PathView.isCurrentItem ? Enums.typography.subtitle : Enums.typography.body
                font.weight: PathView.isCurrentItem ? Font.Medium : Font.Normal
                horizontalAlignment: control.textAlignment
                verticalAlignment: Text.AlignVCenter
                color: {
                    if (PathView.isCurrentItem) {
                        return Enums.textColor.primary
                    }
                    return Enums.stateColor.textMedium
                }
                opacity: PathView.isCurrentItem ? 1 : Math.max(0.3, 1 - distanceFromCenter * 0.6)
            }
        }
    }
    
    // Non-cyclic scrolling list view 非循环滚动 ListView
    ListView {
        id: listView
        anchors.fill: parent
        visible: !control.cycle
        model: control.cycle ? [] : control._safeItems
        clip: true
        interactive: true
        snapMode: ListView.SnapToItem
        highlightRangeMode: ListView.StrictlyEnforceRange
        preferredHighlightBegin: (control.height - control._safeItemHeight) / 2
        preferredHighlightEnd: (control.height + control._safeItemHeight) / 2
        highlightMoveDuration: Enums.duration.medium  // Smooth scroll animation 平滑滚动动画
        maximumFlickVelocity: Enums.controlSize.wheelPickerMaxFlickVelocity
        flickDeceleration: Enums.controlSize.wheelPickerFlickDeceleration
        
        // Add padding so items can scroll to center 添加边距以便项目可以滚动到中心
        header: Item { width: 1; height: (control.height - control._safeItemHeight) / 2 }
        footer: Item { width: 1; height: (control.height - control._safeItemHeight) / 2 }
        
        currentIndex: control._safeCurrentIndex
        onCurrentIndexChanged: {
            if (!control.cycle && control.currentIndex !== currentIndex) {
                control.currentIndex = currentIndex
                control.currentItemChanged(currentIndex, control.currentValue)
            }
        }
        
        delegate: Item {
            property bool isCurrent: index === listView.currentIndex
            property real distanceFromCenter: {
                var center = control.height / 2
                var itemCenter = y - listView.contentY + height / 2
                return control._distanceFromCenter(center, itemCenter)
            }

            width: listView.width
            height: control._safeItemHeight
            // Keep Item instead of Rectangle so transparent delegates do not occlude the popup highlight.
            // 保持 Item，避免透明 Rectangle 委托遮挡弹窗选中高亮。

            Label {
                anchors.centerIn: parent
                type: Enums.label.type_body
                text: String(modelData)
                font.pixelSize: isCurrent ? Enums.typography.subtitle : Enums.typography.body
                font.weight: isCurrent ? Font.Medium : Font.Normal
                horizontalAlignment: control.textAlignment
                verticalAlignment: Text.AlignVCenter
                color: isCurrent ? Enums.textColor.primary : Enums.stateColor.textMedium
                opacity: isCurrent ? 1 : Math.max(0.3, 1 - parent.distanceFromCenter * 0.6)
            }
            
            MouseArea {
                anchors.fill: parent
                onClicked: listView.currentIndex = index
            }
        }
    }
    
    // Mouse and wheel interaction 鼠标与滚轮交互
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        propagateComposedEvents: true
        
        onEntered: control._hovered = true
        onExited: control._hovered = false
        
        onWheel: (wheel) => {
            if (wheel.angleDelta.y > 0) {
                control.scrollUp()
            } else {
                control.scrollDown()
            }
        }
        
        onClicked: (mouse) => {
            // Click to select item 点击选择项目
            var itemIndex = Math.floor(mouse.y / control._safeItemHeight)
            var centerIndex = Math.floor(control._safeVisibleItems / 2)
            var diff = itemIndex - centerIndex
            if (diff !== 0) {
                if (diff > 0) {
                    for (var i = 0; i < diff; i++) control.scrollDown()
                } else {
                    for (var j = 0; j < -diff; j++) control.scrollUp()
                }
            }
        }
    }

    Timer {
        id: repeatTimer

        interval: control._repeatStarted
            ? Enums.duration.wheelPickerRepeatInterval
            : Enums.duration.wheelPickerRepeatDelay
        repeat: true
        onTriggered: control._triggerRepeat()
    }
    
    // Scroll buttons 滚动按钮
    Rectangle {
        id: upButton
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: Enums.controlSize.wheelPickerItemHeight
        color: upArea.containsMouse ? Enums.stateColor.controlBgHover : Enums.transparent
        visible: control.showScrollButtons && control._hovered
        z: Enums.zIndex.popup
        
        Icon {
            anchors.centerIn: parent
            icon: Enums.icon.chevron_up
            iconSize: upArea.pressed ? Enums.iconSize.xs : Enums.iconSize.s
            color: Enums.textColor.secondary
        }
        
        MouseArea {
            id: upArea

            anchors.fill: parent
            hoverEnabled: true

            onClicked: control.scrollUp()
            onPressed: control._startRepeat(-1)
            onReleased: control._stopRepeat(-1)
            onExited: control._stopRepeat(-1)
        }
    }
    
    Rectangle {
        id: downButton
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: Enums.controlSize.wheelPickerItemHeight
        color: downArea.containsMouse ? Enums.stateColor.controlBgHover : Enums.transparent
        visible: control.showScrollButtons && control._hovered
        z: Enums.zIndex.popup
        
        Icon {
            anchors.centerIn: parent
            icon: Enums.icon.chevron_down
            iconSize: downArea.pressed ? Enums.iconSize.xs : Enums.iconSize.s
            color: Enums.textColor.secondary
        }
        
        MouseArea {
            id: downArea

            anchors.fill: parent
            hoverEnabled: true

            onClicked: control.scrollDown()
            onPressed: control._startRepeat(1)
            onReleased: control._stopRepeat(1)
            onExited: control._stopRepeat(1)
        }
    }

}
