// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick.Layouts
import QtQuick.Controls
import "../.."
import QtQuick  // Keep native types unprefixed after library imports 库导入后保留无前缀原生类型
import QtQuick.Window  // Keep native Window unprefixed after library imports 库导入后保留无前缀原生 Window

// Widget - Base component for all PrismQML widgets 所有PrismQML组件的基类
Item {
    id: widget

    // ==================== Public Props 公开属性 ====================
    // Background 背景
    property color backgroundColor: Enums.transparent
    property real backgroundRadius: 0
    property bool centerContent: false  // Center children 子组件居中

    // Size priority system 尺寸优先级系统
    property real preferredWidth: 0
    property real preferredHeight: 0
    property real contentWidth: 0
    property real contentHeight: 0

    // Layout attached properties 布局附加属性
    // Allow parent layout to control fill behavior 允许父布局控制填充行为
    property bool layoutFillWidth: true
    property bool layoutFillHeight: false

    // Tooltip support 工具提示支持
    property string toolTipText: ""
    property int toolTipDuration: Enums.duration.persistent
    property int toolTipShowDelay: Enums.duration.tooltipShowDelay
    property int toolTipHideDelay: Enums.duration.none
    property int toolTipPosition: Enums.position.top

    // ==================== Signals 信号 ====================
    signal _toolTipTimersCanceled()

    // ==================== Public Methods 公开方法 ====================
    // Public methods for tooltip control 公开的tooltip控制方法
    function showToolTip() { if (toolTipText !== "") _toolTip.show() }
    function hideToolTip() {
        _cancelToolTipTimers()
        _toolTip.hide()
    }
    // setParent - Reparent this widget to a new parent 重新设置父组件
    function setParent(newParent) {
        if (newParent && newParent !== widget.parent) {
            widget.parent = newParent
        }
    }

    // addWidget - Add a child widget 添加子组件
    function addWidget(childWidget) {
        if (childWidget) {
            childWidget.parent = widget
        }
    }

    // removeWidget - Remove a child widget 移除子组件
    function removeWidget(childWidget) {
        if (childWidget && childWidget.parent === widget) {
            childWidget.parent = null
        }
    }

    // ==================== Internal Methods 内部方法 ====================
    function _cancelToolTipTimers() {
        _hoverArea._showScheduled = false
        _showTimer.stop()
        _hideTimer.stop()
        _autoHideTimer.stop()
        _toolTipTimersCanceled()
    }
    function _dismissToolTip() {
        _cancelToolTipTimers()
        _toolTip.dismiss()
    }

    clip: false  // Allow tooltip to overflow 允许tooltip溢出显示

    // ==================== Size 尺寸 ====================
    implicitWidth: preferredWidth > 0 ? preferredWidth : contentWidth
    implicitHeight: preferredHeight > 0 ? preferredHeight : contentHeight

    // If no explicit size and parent exists, fill parent width 如果没有显式尺寸且有父容器，填充父容器宽度
    width: preferredWidth > 0 ? preferredWidth : (contentWidth > 0 ? contentWidth : (parent ? parent.width : 0))
    height: preferredHeight > 0 ? preferredHeight : (contentHeight > 0 ? contentHeight : implicitHeight)

    Layout.fillWidth: layoutFillWidth
    Layout.fillHeight: layoutFillHeight

    // Center first child when centerContent is true 当centerContent为true时居中第一个子组件
    onChildrenChanged: if (centerContent) _centerChildrenDelayed.start()
    onCenterContentChanged: if (centerContent) _centerChildrenDelayed.start()

    // ==================== Content 内容 ====================

    Rectangle {
        id: _background
        objectName: "_background"
        anchors.fill: parent
        color: widget.backgroundColor
        radius: widget.backgroundRadius
        visible: widget.backgroundColor.a > 0
    }

    Timer {
        id: _centerChildrenDelayed
        interval: Enums.duration.tick
        onTriggered: {
            for (var i = 0; i < widget.children.length; i++) {
                var child = widget.children[i]
                if (child && child.objectName !== "_background" && child.objectName !== "_toolTip" && child.objectName !== "_hoverArea" && child.objectName !== "_centerChildrenDelayed") {
                    // Center through anchors for broad child compatibility 使用 anchors 居中以兼容不同子组件
                    child.anchors.centerIn = widget
                    break
                }
            }
        }
    }

    // Window-backed tooltip avoids parent clipping and preserves popup z-order 独立窗口工具提示避免父级裁剪并保持弹出层级
    Popup {
        id: _toolTip

        // ==================== Internal Props 内部属性 ====================
        property bool _pendingShow: false

        // ==================== Internal Methods 内部方法 ====================
        function _updatePosition() {
            if (widget.toolTipPosition === Enums.position.right) {
                x = widget.width + Enums.spacing.xs
                y = (widget.height - _toolTip.height) / 2
            } else if (widget.toolTipPosition === Enums.position.bottom) {
                x = (widget.width - _toolTip.width) / 2
                y = widget.height + Enums.spacing.xs
            } else if (widget.toolTipPosition === Enums.position.left) {
                x = -_toolTip.width - Enums.spacing.xs
                y = (widget.height - _toolTip.height) / 2
            } else {
                x = (widget.width - _toolTip.width) / 2
                y = -_toolTip.height - Enums.spacing.xs
            }
        }
        function show() {
            _pendingShow = true
            _updatePosition()
            Qt.callLater(_doOpen)
        }
        function hide() {
            _pendingShow = false
            _toolTip.close()
        }
        function dismiss() {
            _pendingShow = false
            // Explicit dismissal must not overlap a menu with the exit animation.
            // 显式隐藏不能让退出动画继续与菜单重叠显示。
            // Qt ignores a second close() while an exit transition is already running.
            // Re-open without transitions to cancel that exit, then close synchronously.
            // Qt 在退出动画运行时会忽略第二次 close()；先无动画重开以取消退出，再同步关闭。
            var enterTransition = _toolTip.enter
            var exitTransition = _toolTip.exit
            _toolTip.enter = null
            _toolTip.exit = null
            if (_toolTip.visible) {
                _toolTip.open()
                _toolTip.close()
            }
            _toolTip.enter = enterTransition
            _toolTip.exit = exitTransition
        }
        function _doOpen() {
            if (!_pendingShow) return
            _toolTip.open()
        }

        objectName: "_toolTip"

        // Use a separate OS window to cross Window bounds without clipping 使用独立 OS 窗口跨越 Window 边界且不被裁剪
        // Qt 6.7+ supports this path for compact floating windows Qt 6.7+ 支持紧凑浮窗使用此路径
        popupType: Popup.Window

        // Allow the popup to exceed window bounds 允许弹窗超出窗口边界
        margins: -1
        leftPadding: Enums.spacing.l
        rightPadding: Enums.spacing.l
        topPadding: Enums.spacing.xs
        bottomPadding: Enums.spacing.xs
        closePolicy: Popup.NoAutoClose
        clip: false

        width: _tooltipMetrics.width + leftPadding + rightPadding
        height: Enums.controlSize.tooltipHeight

        background: Rectangle {
            radius: Enums.isPrismDesign ? Enums.prismDesign.radiusPopup : Enums.radius.small
            color: Enums.isPrismDesign ? Enums.dialogColor : Enums.cardColor
            // Use borderStrong so the outline stays visible on light backgrounds 使用 borderStrong 保持浅色背景上的描边可见
            border.width: Enums.border.thin
            border.color: Enums.stateColor.borderStrong
        }

        contentItem: Item {
            Text {
                id: _tooltipText
                anchors.centerIn: parent
                text: widget.toolTipText
                font.pixelSize: Enums.typography.caption
                font.family: Enums.fontFamily
                color: Enums.foregroundColor
            }
        }
        enter: Transition {
            ParallelAnimation {
                NumberAnimation { property: "opacity"; from: 0.0; to: 1.0; duration: Enums.duration.normal }
                NumberAnimation { property: "scale"; from: 0.8; to: 1.0; duration: Enums.duration.normal; easing.type: Easing.OutBack }
            }
        }
        exit: Transition {
            ParallelAnimation {
                NumberAnimation { property: "opacity"; from: 1.0; to: 0.0; duration: Enums.duration.normal }
                NumberAnimation { property: "scale"; from: 1.0; to: 0.8; duration: Enums.duration.normal }
            }
        }

        // Keep metrics outside contentItem so lazy content does not affect them 将度量对象置于 contentItem 外避免受懒加载影响
        TextMetrics {
            id: _tooltipMetrics
            text: widget.toolTipText
            font.pixelSize: Enums.typography.caption
            font.family: Enums.fontFamily
        }
    }

    // Hover detection 悬停检测
    MouseArea {
        id: _hoverArea

        // ==================== Internal Props 内部属性 ====================
        property bool _showScheduled: false

        objectName: "_hoverArea"
        anchors.fill: parent
        hoverEnabled: widget.toolTipText !== ""
        acceptedButtons: Qt.NoButton
        propagateComposedEvents: true

        onEntered: {
            if (widget.toolTipText !== "") {
                _showScheduled = true
                _showTimer.start()
            }
        }
        onExited: {
            _showScheduled = false
            _showTimer.stop()
            _hideTimer.start()
        }
    }
    
    Timer {
        id: _showTimer
        interval: widget.toolTipShowDelay
        onTriggered: {
            if (_hoverArea._showScheduled) {
                _toolTip.show()
                if (widget.toolTipDuration > 0) {
                    _autoHideTimer.interval = widget.toolTipDuration
                    _autoHideTimer.start()
                }
            }
        }
    }
    
    Timer {
        id: _hideTimer
        interval: widget.toolTipHideDelay
        onTriggered: _toolTip.hide()
    }
    
    Timer {
        id: _autoHideTimer
        onTriggered: _toolTip.hide()
    }
}
