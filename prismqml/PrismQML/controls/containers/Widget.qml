// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick.Layouts
import "../.."
import "../../SkinResolver.js" as SkinResolver
import "_internal" as ContainerInternal
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

    // Skin context 皮肤上下文
    // Advanced entry for popups, reparented content, and tests. Normal pages
    // only write `SkinScope`; children then resolve the nearest scope through
    // their visual parent chain.
    // 供弹出层、跨父级重挂载内容与测试使用的高级入口。普通页面只写 `SkinScope`，
    // 子项随后通过视觉父级链解析最近的范围。
    property var skinContext: null
    // Explicit value wins, then the nearest SkinScope, then the global Enums.
    // 显式值优先，其次最近 SkinScope，最后是全局 Enums。
    readonly property var effectiveSkinContext: skinContext || _nearestSkinContext || Enums
    // Only an explicit bridge is published to descendants. Automatic scope
    // lookup remains local to every widget so child creation order cannot
    // transiently replace a real ancestor SkinScope with global Enums.
    // 仅把显式桥接发布给后代。自动范围查找仍由每个控件自行完成，避免子项创建顺序
    // 暂时以全局 Enums 覆盖真实祖先 SkinScope。
    readonly property var _prismSkinScopeContext: skinContext || null

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
    // Resolved nearest scope; null when no ancestor SkinScope exists.
    // 解析出的最近范围；没有祖先 SkinScope 时为 null。
    property var _nearestSkinContext: null
    readonly property Loader _centerChildrenDelayed: Loader {
        active: widget.centerContent
        onLoaded: widget._scheduleCenterChildren()

        sourceComponent: ContainerInternal.WidgetCenterChildrenTimer {
            host: widget
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
    // Runs on creation, reparenting, and explicit context changes only — never
    // per frame, per hover, or inside animation callbacks.
    // 只在创建、重挂载与显式上下文变化时执行，不在每帧、hover 或动画回调内执行。
    function _resolveSkinContext() {
        if (widget.skinContext) {
            widget._nearestSkinContext = null
            return
        }
        widget._nearestSkinContext = SkinResolver.nearestContext(widget.parent)
    }

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

    // Skin context resolution 皮肤上下文解析
    onParentChanged: widget._resolveSkinContext()
    onSkinContextChanged: widget._resolveSkinContext()
    Component.onCompleted: widget._resolveSkinContext()

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
