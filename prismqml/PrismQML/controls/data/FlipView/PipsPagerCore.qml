// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../buttons"

// PipsPagerCore - Pips pager base class 分页指示器基类
// Features: scroll buttons, visible number limit, smooth scroll 功能：翻页按钮、可见数量限制、平滑滚动
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int count: 5
    property int currentIndex: 0
    property bool vertical: false
    property bool interactive: true
    property int maxVisible: 5  // Max visible pips 最大可见点数
    property int prevButtonMode: Enums.pipsPager.button_never
    property int nextButtonMode: Enums.pipsPager.button_never
    
    // ==================== Internal Props 内部属性 ====================
    readonly property int _cellSize: Enums.spacing.l
    readonly property int _normalRadius: Enums.radius.tiny
    readonly property int _activeRadius: Enums.radius.tiny + 1
    readonly property int _normalDiameter: _normalRadius
    readonly property int _activeDiameter: _activeRadius * 2
    readonly property color _pipActiveColor: Enums.stateColor.pipActive
    readonly property color _pipInactiveColor: Enums.stateColor.pipNormal
    readonly property color _pipHoverColor: Enums.stateColor.pipActive
    readonly property int _buttonSize: _cellSize
    readonly property int _visibleCount: Math.min(count, maxVisible)
    readonly property int _pipCount: Math.max(0, count)
    readonly property bool _hasPrevButton: prevButtonMode !== Enums.pipsPager.button_never
    readonly property bool _hasNextButton: nextButtonMode !== Enums.pipsPager.button_never
    property Item _prevButton: null
    property Item _nextButton: null

    // ==================== Signals 信号 ====================
    signal indexClicked(int index)

    // ==================== Public Methods 公开方法 ====================
    function next() { if (currentIndex < count - 1) currentIndex++ }
    function previous() { if (currentIndex > 0) currentIndex-- }
    function setCurrentIndex(index) { if (index >= 0 && index < count) currentIndex = index }

    // Get current index 获取当前索引
    function getCurrentIndex() { return currentIndex }

    // ==================== Internal Methods 内部方法 ====================
    // 翻页按钮仅在"模式非 never"且"当前页留有余量"时显示。
    // 正向布尔表达: mode 先行短路, 再看 index 是否还有可翻空间。
    function _isPrevButtonVisible() {
        return prevButtonMode !== Enums.pipsPager.button_never && currentIndex > 0
    }

    function _isNextButtonVisible() {
        return nextButtonMode !== Enums.pipsPager.button_never && currentIndex < (count - 1)
    }

    // Synchronize a navigation button with its public mode.
    // 按公开模式同步单个翻页按钮的生命周期。
    function _syncNavButton(isNext) {
        const mode = isNext ? nextButtonMode : prevButtonMode
        const shouldExist = mode !== Enums.pipsPager.button_never
        const currentButton = isNext ? _nextButton : _prevButton
        if ((shouldExist && currentButton) || (!shouldExist && !currentButton)) return

        if (shouldExist) {
            const button = navButtonComponent.createObject(control, { "isNext": isNext })
            if (!button) {
                console.error(
                    "PipsPagerCore: failed to create " +
                    (isNext ? "next" : "previous") + " navigation button"
                )
                return
            }
            if (isNext) _nextButton = button
            else _prevButton = button
            return
        }

        if (isNext) _nextButton = null
        else _prevButton = null
        currentButton.destroy()
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: vertical ? _cellSize : _visibleCount * _cellSize + (_hasPrevButton ? _buttonSize : 0) + (_hasNextButton ? _buttonSize : 0)
    implicitHeight: vertical ? _visibleCount * _cellSize + (_hasPrevButton ? _buttonSize : 0) + (_hasNextButton ? _buttonSize : 0) : _cellSize

    on_HasPrevButtonChanged: _syncNavButton(false)
    on_HasNextButtonChanged: _syncNavButton(true)

    // ==================== Content 内容 ====================
    // Wheel support 滚轮支持
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
    
    // Shared factory for navigation buttons enabled by the public modes.
    // 公开模式启用翻页按钮时使用的共享工厂。
    Component {
        id: navButtonComponent

        ButtonCore {
            id: navButton

            required property bool isNext

            objectName: isNext ? "pipsNextButton" : "pipsPrevButton"
            visible: isNext
                ? control._isNextButtonVisible()
                : control._isPrevButtonVisible()
            style: Enums.button.style_transparent
            shape: Enums.button.shape_pill
            icon: control.vertical
                ? (isNext ? Enums.icon.chevron_down : Enums.icon.chevron_up)
                : (isNext ? Enums.icon.chevron_right : Enums.icon.chevron_left)
            iconSize: Enums.iconSize.micro
            width: control._buttonSize
            height: control._buttonSize

            anchors {
                left: !control.vertical && !isNext ? parent.left : undefined
                right: !control.vertical && isNext ? parent.right : undefined
                top: control.vertical && !isNext ? parent.top : undefined
                bottom: control.vertical && isNext ? parent.bottom : undefined
                horizontalCenter: control.vertical ? parent.horizontalCenter : undefined
                verticalCenter: control.vertical ? undefined : parent.verticalCenter
            }

            onClicked: {
                if (isNext) control.next()
                else control.previous()
            }
        }
    }
    
    // Pips container 点容器
    Item {
        id: pipsContainer
        clip: true
        
        anchors {
            left: vertical || !control._prevButton || !control._prevButton.visible
                ? parent.left : control._prevButton.right
            right: vertical || !control._nextButton || !control._nextButton.visible
                ? parent.right : control._nextButton.left
            top: !vertical || !control._prevButton || !control._prevButton.visible
                ? parent.top : control._prevButton.bottom
            bottom: !vertical || !control._nextButton || !control._nextButton.visible
                ? parent.bottom : control._nextButton.top
        }
        
        // Shared horizontal/vertical pips layout 横竖方向共享点布局
        Item {
            id: pipsLayout

            property real _scrollOffset: {
                if (count <= maxVisible) return 0
                var centerOffset = currentIndex - Math.floor(maxVisible / 2)
                var maxOffset = count - maxVisible
                return Math.max(0, Math.min(centerOffset, maxOffset)) * _cellSize
            }
            property real _animatedScrollOffset: _scrollOffset

            width: control._pipCount > 0
                ? (control.vertical ? control._cellSize : control._pipCount * control._cellSize)
                : 0
            height: control._pipCount > 0
                ? (control.vertical ? control._pipCount * control._cellSize : control._cellSize)
                : 0
            x: control.vertical
                ? (parent.width - width) / 2
                : -_animatedScrollOffset
            y: control.vertical
                ? -_animatedScrollOffset
                : (parent.height - height) / 2

            Behavior on _animatedScrollOffset {
                NumberAnimation {
                    duration: Enums.duration.medium
                    easing.type: Easing.OutCubic
                }
            }

            Repeater {
                model: control._pipCount

                Item {
                    width: control._cellSize
                    height: control._cellSize
                    x: control.vertical ? 0 : index * control._cellSize
                    y: control.vertical ? index * control._cellSize : 0

                    Rectangle {
                        anchors.centerIn: parent
                        width: (index === control.currentIndex || pipMouse.containsMouse) ? control._activeDiameter : control._normalDiameter
                        height: width
                        radius: width / 2
                        color: index === control.currentIndex
                               ? control._pipActiveColor
                               : (pipMouse.containsMouse ? control._pipHoverColor : control._pipInactiveColor)

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
    }
    
}
