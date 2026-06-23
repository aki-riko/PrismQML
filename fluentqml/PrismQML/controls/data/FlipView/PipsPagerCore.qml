// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../buttons"

// PipsPagerCore - Pips pager base class 分页指示器基类
// Features: scroll buttons, visible number limit, smooth scroll 功能：翻页按钮、可见数量限制、平滑滚动
Item {
    id: control
    
    // ==================== Public Properties 公开属性 ====================
    property int count: 5
    property int currentIndex: 0
    property bool vertical: false
    property bool interactive: true
    property int maxVisible: 5  // Max visible pips 最大可见点数
    property int prevButtonMode: Enums.pipsPager.button_never
    property int nextButtonMode: Enums.pipsPager.button_never
    
    // ==================== Signals 信号 ====================
    signal indexClicked(int index)
    
    // ==================== Internal 内部 ====================
    readonly property int _cellSize: Enums.spacing.l
    readonly property int _normalRadius: Enums.radius.tiny
    readonly property int _activeRadius: Enums.radius.tiny + 1
    readonly property int _buttonSize: _cellSize
    readonly property int _visibleCount: Math.min(count, maxVisible)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: vertical ? _cellSize : _visibleCount * _cellSize + (_hasPrevButton ? _buttonSize : 0) + (_hasNextButton ? _buttonSize : 0)
    implicitHeight: vertical ? _visibleCount * _cellSize + (_hasPrevButton ? _buttonSize : 0) + (_hasNextButton ? _buttonSize : 0) : _cellSize
    
    readonly property bool _hasPrevButton: prevButtonMode !== Enums.pipsPager.button_never
    readonly property bool _hasNextButton: nextButtonMode !== Enums.pipsPager.button_never

    // ==================== Button Visibility Logic 按钮可见性逻辑 ====================
    // 翻页按钮仅在"模式非 never"且"当前页留有余量"时显示。
    // 正向布尔表达: mode 先行短路, 再看 index 是否还有可翻空间。
    function _isPrevButtonVisible() {
        return prevButtonMode !== Enums.pipsPager.button_never && currentIndex > 0
    }

    function _isNextButtonVisible() {
        return nextButtonMode !== Enums.pipsPager.button_never && currentIndex < (count - 1)
    }

    // ==================== Public Methods 公开方法 ====================
    function next() { if (currentIndex < count - 1) currentIndex++ }
    function previous() { if (currentIndex > 0) currentIndex-- }
    function setCurrentIndex(index) { if (index >= 0 && index < count) currentIndex = index }

    // Get current index 获取当前索引
    function getCurrentIndex() { return currentIndex }

    // ==================== Wheel Support 滚轮支持 ====================
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        
        onWheel: (wheel) => {
            // Use angleDelta.y for both horizontal and vertical pager 统一使用angleDelta.y处理滚轮

            if (wheel.angleDelta.y > 0) {
                control.previous()
            } else if (wheel.angleDelta.y < 0) {
                control.next()
            }
        }
    }
    
    // ==================== Previous Button 上一页按钮 ====================
    ButtonCore {
        id: prevButton
        visible: _isPrevButtonVisible()
        style: Enums.button.style_transparent
        shape: Enums.button.shape_pill
        icon: vertical ? Enums.icon.chevron_up : Enums.icon.chevron_left
        iconSize: Enums.iconSize.micro
        width: _buttonSize
        height: _buttonSize
        
        anchors {
            left: vertical ? undefined : parent.left
            top: vertical ? parent.top : undefined
            horizontalCenter: vertical ? parent.horizontalCenter : undefined
            verticalCenter: vertical ? undefined : parent.verticalCenter
        }
        
        onClicked: control.previous()
    }
    
    // ==================== Pips Container 点容器 ====================
    Item {
        id: pipsContainer
        clip: true
        
        anchors {
            left: vertical ? parent.left : (prevButton.visible ? prevButton.right : parent.left)
            right: vertical ? parent.right : (nextButton.visible ? nextButton.left : parent.right)
            top: vertical ? (prevButton.visible ? prevButton.bottom : parent.top) : parent.top
            bottom: vertical ? (nextButton.visible ? nextButton.top : parent.bottom) : parent.bottom
        }
        
        // Horizontal pips 水平点
        Row {
            id: hRow
            visible: !control.vertical
            y: (parent.height - height) / 2
            x: -_scrollOffset
            
            property real _scrollOffset: {
                if (count <= maxVisible) return 0
                var centerOffset = currentIndex - Math.floor(maxVisible / 2)
                var maxOffset = count - maxVisible
                return Math.max(0, Math.min(centerOffset, maxOffset)) * _cellSize
            }
            
            Behavior on x { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic } }
            
            Repeater {
                model: control.count
                
                Item {
                    width: control._cellSize
                    height: control._cellSize
                    
                    Rectangle {
                        anchors.centerIn: parent
                        width: (index === control.currentIndex || pipMouse.containsMouse) ? control._activeRadius * 2 : control._normalRadius * 2
                        height: width
                        radius: width / 2
                        color: (index === control.currentIndex || pipMouse.containsMouse) ? Enums.stateColor.pipActive : Enums.stateColor.pipNormal
                        
                        Behavior on width { NumberAnimation { duration: Enums.duration.fast } }
                        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                    }
                    
                    MouseArea {
                        id: pipMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (control.interactive) control.currentIndex = index
                            control.indexClicked(index)
                        }
                    }
                }
            }
        }

        // Vertical pips 垂直点
        Column {
            id: vCol
            visible: control.vertical
            x: (parent.width - width) / 2
            y: -_scrollOffset
            
            property real _scrollOffset: {
                if (count <= maxVisible) return 0
                var centerOffset = currentIndex - Math.floor(maxVisible / 2)
                var maxOffset = count - maxVisible
                return Math.max(0, Math.min(centerOffset, maxOffset)) * _cellSize
            }
            
            Behavior on y { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic } }
            
            Repeater {
                model: control.count
                
                Item {
                    width: control._cellSize
                    height: control._cellSize
                    
                    Rectangle {
                        anchors.centerIn: parent
                        width: (index === control.currentIndex || pipMouseV.containsMouse) ? control._activeRadius * 2 : control._normalRadius * 2
                        height: width
                        radius: width / 2
                        color: (index === control.currentIndex || pipMouseV.containsMouse) ? Enums.stateColor.pipActive : Enums.stateColor.pipNormal
                        
                        Behavior on width { NumberAnimation { duration: Enums.duration.fast } }
                        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                    }
                    
                    MouseArea {
                        id: pipMouseV
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (control.interactive) control.currentIndex = index
                            control.indexClicked(index)
                        }
                    }
                }
            }
        }
    }
    
    // ==================== Next Button 下一页按钮 ====================
    ButtonCore {
        id: nextButton
        visible: _isNextButtonVisible()
        style: Enums.button.style_transparent
        shape: Enums.button.shape_pill
        icon: vertical ? Enums.icon.chevron_down : Enums.icon.chevron_right
        iconSize: Enums.iconSize.micro
        width: _buttonSize
        height: _buttonSize
        
        anchors {
            right: vertical ? undefined : parent.right
            bottom: vertical ? parent.bottom : undefined
            horizontalCenter: vertical ? parent.horizontalCenter : undefined
            verticalCenter: vertical ? undefined : parent.verticalCenter
        }
        
        onClicked: control.next()
    }
}
