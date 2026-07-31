// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick.Layouts
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
    // Horizontal text alignment inside the tooltip (Qt Text enum) 提示内文本水平对齐(Qt Text 枚举),默认左对齐
    property int toolTipTextAlignment: Text.AlignLeft

    // ==================== Internal Props 内部属性 ====================
    property bool _toolTipShowPending: false
    readonly property Loader _centerChildrenDelayed: Loader {
        active: widget.centerContent
        onLoaded: widget._scheduleCenterChildren()

        sourceComponent: Timer {
            interval: Enums.duration.tick
            onTriggered: {
                for (var i = 0; i < widget.children.length; i++) {
                    var child = widget.children[i]
                    if (widget._isCenterableChild(child)) {
                        // Center through anchors for broad child compatibility 使用锚点居中以兼容不同子项。
                        child.anchors.centerIn = widget
                        break
                    }
                }
            }
        }
    }

    // ==================== Signals 信号 ====================
    signal _toolTipTimersCanceled()

    // ==================== Public Methods 公开方法 ====================
    // Public methods for tooltip control 公开的tooltip控制方法
    function showToolTip() {
        if (toolTipText === "") return
        _toolTipShowPending = true
        if (_toolTipLoader.item) _toolTipLoader.item.showToolTip()
    }

    function hideToolTip() {
        _cancelToolTipTimers()
        if (_toolTipLoader.item) _toolTipLoader.item.hideToolTip()
        else _toolTipShowPending = false
    }

    // setParent - Reparent this widget to a new parent 重新设置父组件
    function setParent(newParent) {
        if (newParent && newParent !== widget.parent) widget.parent = newParent
    }

    // addWidget - Add a child widget 添加子组件
    function addWidget(childWidget) {
        if (childWidget) childWidget.parent = widget
    }

    // removeWidget - Remove a child widget 移除子组件
    function removeWidget(childWidget) {
        if (childWidget && childWidget.parent === widget) childWidget.parent = null
    }

    // ==================== Internal Methods 内部方法 ====================
    function _cancelToolTipTimers() {
        if (_toolTipLoader.item) _toolTipLoader.item.cancelTimers()
        _toolTipTimersCanceled()
    }

    function _startToolTipShowTimer() {
        if (_toolTipLoader.item) _toolTipLoader.item.startShowTimer()
    }

    function _stopToolTipShowTimer() {
        if (_toolTipLoader.item) _toolTipLoader.item.stopShowTimer()
    }

    function _dismissToolTip() {
        _cancelToolTipTimers()
        if (_toolTipLoader.item) _toolTipLoader.item.dismissToolTip()
        else _toolTipShowPending = false
    }

    function _isCenterableChild(child) {
        if (!child) return false
        var name = child.objectName
        return name !== "_background" &&
               name !== "_toolTipLoader" &&
               name !== "_centerChildrenDelayed"
    }

    function _scheduleCenterChildren() {
        if (_centerChildrenDelayed.item) _centerChildrenDelayed.item.start()
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
    onChildrenChanged: if (centerContent) _scheduleCenterChildren()
    onCenterContentChanged: if (centerContent) _scheduleCenterChildren()

    // ==================== Content 内容 ====================

    Rectangle {
        id: _background
        objectName: "_background"
        anchors.fill: parent
        color: widget.backgroundColor
        radius: widget.backgroundRadius
        visible: widget.backgroundColor.a > 0
    }

    Loader {
        id: _toolTipLoader
        objectName: "_toolTipLoader"
        anchors.fill: parent
        active: widget.toolTipText !== ""
        source: "_internal/WidgetToolTipSupport.qml"

        onLoaded: {
            if (!item) return
            item.widget = widget
            if (widget._toolTipShowPending) item.showToolTip()
        }
    }
}
