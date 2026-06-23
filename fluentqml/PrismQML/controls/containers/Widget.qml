// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick.Layouts
import QtQuick.Controls
import "../.."
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖
import QtQuick.Window  // 置于库import后:去前缀后保原生Window不被库覆盖

// Widget - Base component for all FluentQML widgets 所有FluentQML组件的基类
Item {
    id: widget
    clip: false  // Allow tooltip to overflow 允许tooltip溢出显示

    // ==================== Size Priority System 尺寸优先级系统 ====================
    property real preferredWidth: 0
    property real preferredHeight: 0
    property real contentWidth: 0
    property real contentHeight: 0

    implicitWidth: preferredWidth > 0 ? preferredWidth : contentWidth
    implicitHeight: preferredHeight > 0 ? preferredHeight : contentHeight
    
    // When preferredWidth/Height is set, also set width/height for child components 当设置preferredWidth/Height时，同时设置width/height供子组件使用

    // If no explicit size and parent exists, fill parent width 如果没有显式尺寸且有父容器，填充父容器宽度
    width: preferredWidth > 0 ? preferredWidth : (contentWidth > 0 ? contentWidth : (parent ? parent.width : 0))
    height: preferredHeight > 0 ? preferredHeight : (contentHeight > 0 ? contentHeight : implicitHeight)
    
    // ==================== Layout attached properties 布局附加属性 ====================
    // Allow parent layout to control fill behavior 允许父布局控制填充行为
    property bool layoutFillWidth: true
    property bool layoutFillHeight: false
    Layout.fillWidth: layoutFillWidth
    Layout.fillHeight: layoutFillHeight

    // ==================== Background 背景 ====================
    property color backgroundColor: "transparent"
    property real backgroundRadius: 0
    property bool centerContent: false  // Center children 子组件居中

    // ==================== ToolTip Support 工具提示支持 ====================
    property string toolTipText: ""
    property int toolTipDuration: -1
    property int toolTipShowDelay: 500
    property int toolTipHideDelay: 0

    // ==================== Public Methods 公开方法 ====================
    // Public methods for tooltip control 公开的tooltip控制方法
    function showToolTip() { if (toolTipText !== "") _toolTip.show() }
    function hideToolTip() { _toolTip.hide() }

    // ==================== Widget Methods 组件方法 ====================
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

    Rectangle {
        id: _background
        objectName: "_background"
        anchors.fill: parent
        color: widget.backgroundColor
        radius: widget.backgroundRadius
        visible: widget.backgroundColor.a > 0
    }
    
    // Center first child when centerContent is true 当centerContent为true时居中第一个子组件
    onChildrenChanged: if (centerContent) _centerChildrenDelayed.start()
    onCenterContentChanged: if (centerContent) _centerChildrenDelayed.start()
    
    Timer {
        id: _centerChildrenDelayed
        interval: Enums.duration.tick
        onTriggered: {
            for (var i = 0; i < widget.children.length; i++) {
                var child = widget.children[i]
                if (child && child.objectName !== "_background" && child.objectName !== "_toolTip" && child.objectName !== "_hoverArea" && child.objectName !== "_centerChildrenDelayed") {
                    // Use x/y positioning instead of anchors for compatibility 使用x/y定位替代anchors以兼容各种组件

                    child.anchors.centerIn = widget
                    break
                }
            }
        }
    }

    // ==================== ToolTip Support 工具提示支持 ====================

    // Inline ToolTip 内联ToolTip

    // Reparent to Window.contentItem for proper z-order (like PopupWindowCore) 挂载到Window.contentItem以正确显示层级（类似PopupWindowCore）

    Popup {
        id: _toolTip
        objectName: "_toolTip"

        // 落到独立 OS 窗口,跨 Window 边界显示,不被父 Window 裁剪
        // (Qt 6.7+ 支持;便签等浮窗顶部空间小,tooltip 越界会被裁)
        popupType: Popup.Window

        // 允许超出窗口边界
        margins: -1
        padding: 0
        closePolicy: Popup.NoAutoClose
        clip: false
        
        // TextMetrics 不在 contentItem 中，不受懒加载影响
        TextMetrics {
            id: _tooltipMetrics
            text: widget.toolTipText
            font.pixelSize: Enums.typography.caption
            font.family: Enums.fontFamily
        }
        
        width: _tooltipMetrics.width + Enums.spacing.xxxl
        height: Enums.controlSize.tooltipHeight
        
        background: Rectangle {
            radius: Enums.radius.small
            color: Enums.cardColor
            // 描边: 用 borderStrong (而非 borderLight),避免在浅色背景上几乎不可见
            border.width: Enums.border.thin
            border.color: Enums.stateColor.borderStrong
        }
        
        contentItem: Item {
            Text {
                id: _tooltipText
                anchors.centerIn: parent
                text: widget.toolTipText
                font.pixelSize: Enums.typography.caption
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
        
        property bool _pendingShow: false
        
        function show() {
            _pendingShow = true
            x = (widget.width - _toolTip.width) / 2
            y = -_toolTip.height - Enums.spacing.xs
            Qt.callLater(_doOpen)
        }
        function hide() {
            _pendingShow = false
            _toolTip.close()
        }
        function _doOpen() {
            if (!_pendingShow) return
            _toolTip.open()
        }
    }

    // Hover detection 悬停检测
    MouseArea {
        id: _hoverArea
        objectName: "_hoverArea"
        anchors.fill: parent
        hoverEnabled: widget.toolTipText !== ""
        acceptedButtons: Qt.NoButton
        propagateComposedEvents: true
        
        property bool _showScheduled: false
        
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
