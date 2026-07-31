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
    // Horizontal text alignment inside the tooltip (Qt Text enum) 提示内文本水平对齐(Qt Text 枚举),默认左对齐
    property int toolTipTextAlignment: Text.AlignLeft

    // ==================== Internal Props 内部属性 ====================
    property bool _toolTipShowPending: false

    // ==================== Signals 信号 ====================
    signal _toolTipTimersCanceled()

    // ==================== Public Methods 公开方法 ====================
    // Public methods for tooltip control 公开的tooltip控制方法
    function showToolTip() {
        if (toolTipText === "") return
        _toolTipShowPending = true
        if (_toolTipLoader.item) _toolTipLoader.item.show()
    }

    function hideToolTip() {
        _cancelToolTipTimers()
        if (_toolTipLoader.item) _toolTipLoader.item.hide()
        else _toolTipShowPending = false
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
        if (_hoverAreaLoader.item) _hoverAreaLoader.item._showScheduled = false
        if (_toolTipLoader.item) _toolTipLoader.item.cancelTimers()
        _toolTipTimersCanceled()
    }

    function _dismissToolTip() {
        _cancelToolTipTimers()
        if (_toolTipLoader.item) _toolTipLoader.item.dismiss()
        else _toolTipShowPending = false
    }

    function _isCenterableChild(child) {
        if (!child) return false
        var name = child.objectName
        return name !== "_background" &&
               name !== "_toolTipLoader" &&
               name !== "_hoverAreaLoader" &&
               name !== "_centerChildrenDelayed"
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
                if (widget._isCenterableChild(child)) {
                    // Center through anchors for broad child compatibility 使用 anchors 居中以兼容不同子组件
                    child.anchors.centerIn = widget
                    break
                }
            }
        }
    }

    Loader {
        id: _toolTipLoader
        objectName: "_toolTipLoader"
        active: widget.toolTipText !== ""

        onLoaded: if (widget._toolTipShowPending && item) item.show()

        // Window-backed tooltip avoids parent clipping and preserves popup z-order 独立窗口工具提示避免父级裁剪并保持弹出层级
        sourceComponent: Popup {
            id: _toolTip

            // ==================== Internal Props 内部属性 ====================
            property bool _pendingShow: false

            // ==================== Internal Methods 内部方法 ====================
            function _screenBounds(sourcePos) {
                var screenGeometry = WindowHelper.availableScreenGeometryAt(
                    Math.round(sourcePos.x + widget.width / 2),
                    Math.round(sourcePos.y + widget.height / 2))
                if (screenGeometry && screenGeometry.width > 0 && screenGeometry.height > 0) {
                    return {
                        left: screenGeometry.x,
                        top: screenGeometry.y,
                        right: screenGeometry.x + screenGeometry.width,
                        bottom: screenGeometry.y + screenGeometry.height
                    }
                }
                return {
                    left: widget.Screen.virtualX,
                    top: widget.Screen.virtualY,
                    right: widget.Screen.virtualX + widget.Screen.width,
                    bottom: widget.Screen.virtualY + widget.Screen.height
                }
            }
            function _directionOrder() {
                if (widget.toolTipPosition === Enums.position.right)
                    return [Enums.position.right, Enums.position.left,
                            Enums.position.top, Enums.position.bottom]
                if (widget.toolTipPosition === Enums.position.left)
                    return [Enums.position.left, Enums.position.right,
                            Enums.position.top, Enums.position.bottom]
                if (widget.toolTipPosition === Enums.position.bottom)
                    return [Enums.position.bottom, Enums.position.top,
                            Enums.position.right, Enums.position.left]
                return [Enums.position.top, Enums.position.bottom,
                        Enums.position.right, Enums.position.left]
            }
            function _directionFits(direction, sourcePos, bounds) {
                var gap = Enums.spacing.xs
                if (direction === Enums.position.right)
                    return sourcePos.x + widget.width + gap + _toolTip.width <= bounds.right
                if (direction === Enums.position.left)
                    return sourcePos.x - gap - _toolTip.width >= bounds.left
                if (direction === Enums.position.bottom)
                    return sourcePos.y + widget.height + gap + _toolTip.height <= bounds.bottom
                return sourcePos.y - gap - _toolTip.height >= bounds.top
            }
            function _resolvedDirection(sourcePos, bounds) {
                var order = _directionOrder()
                for (var i = 0; i < order.length; i++) {
                    if (_directionFits(order[i], sourcePos, bounds))
                        return order[i]
                }
                return order[0]
            }
            function _clamp(value, minimum, maximum) {
                return Math.max(minimum, Math.min(value, maximum))
            }
            function _applyPosition(direction, sourcePos, bounds) {
                var gap = Enums.spacing.xs
                if (direction === Enums.position.right || direction === Enums.position.left) {
                    x = direction === Enums.position.right
                        ? widget.width + gap : -_toolTip.width - gap
                    var globalY = sourcePos.y + (widget.height - _toolTip.height) / 2
                    y = _clamp(globalY, bounds.top,
                               Math.max(bounds.top, bounds.bottom - _toolTip.height)) - sourcePos.y
                    return
                }
                y = direction === Enums.position.bottom
                    ? widget.height + gap : -_toolTip.height - gap
                var globalX = sourcePos.x + (widget.width - _toolTip.width) / 2
                x = _clamp(globalX, bounds.left,
                           Math.max(bounds.left, bounds.right - _toolTip.width)) - sourcePos.x
            }
            function _updatePosition() {
                var sourcePos = widget.mapToGlobal(0, 0)
                var bounds = _screenBounds(sourcePos)
                _applyPosition(_resolvedDirection(sourcePos, bounds), sourcePos, bounds)
            }
            function show() {
                widget._toolTipShowPending = false
                _pendingShow = true
                _updatePosition()
                Qt.callLater(_doOpen)
            }
            function hide() {
                widget._toolTipShowPending = false
                _pendingShow = false
                _toolTip.close()
            }
            function dismiss() {
                widget._toolTipShowPending = false
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
            function startShowTimer() {
                _showTimer.start()
            }
            function stopShowTimer() {
                _showTimer.stop()
            }
            function startHideTimer() {
                _hideTimer.start()
            }
            function cancelTimers() {
                _showTimer.stop()
                _hideTimer.stop()
                _autoHideTimer.stop()
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

            // Width follows text but caps at tooltipMaxWidth to trigger wrapping 宽度跟随文本但以 tooltipMaxWidth 封顶以触发换行
            width: Math.min(_tooltipMetrics.width, Enums.controlSize.tooltipMaxWidth) + leftPadding + rightPadding
            // Height adapts to (possibly wrapped) content, never smaller than one line 高度自适应(可能换行的)内容,不小于单行高
            height: Math.max(Enums.controlSize.tooltipHeight, _tooltipText.implicitHeight + topPadding + bottomPadding)

            background: Rectangle {
                radius: Enums.radius.small
                color: Enums.cardColor
                // Use borderStrong so the outline stays visible on light backgrounds 使用 borderStrong 保持浅色背景上的描边可见
                border.width: Enums.border.thin
                border.color: Enums.stateColor.borderStrong
            }

            contentItem: Text {
                id: _tooltipText
                text: widget.toolTipText
                font.pixelSize: Enums.typography.caption
                font.family: Enums.fontFamily
                color: Enums.foregroundColor
                // Wrap long text within max width; \n still forces line breaks 超过最大宽度自动换行;\n 仍强制断行
                wrapMode: Text.Wrap
                // Alignment exposed via toolTipTextAlignment (default left) 对齐由 toolTipTextAlignment 暴露(默认左对齐)
                horizontalAlignment: widget.toolTipTextAlignment
                verticalAlignment: Text.AlignVCenter
                width: Math.min(_tooltipMetrics.width, Enums.controlSize.tooltipMaxWidth)
            }
            enter: Transition {
                ParallelAnimation {
                    NumberAnimation { property: "opacity"; from: 0.0; to: 1.0; duration: Enums.duration.normal }
                    NumberAnimation { property: "scale"; from: 0.8; to: 1.0; duration: Enums.duration.normal; easing.type: Easing.OutCubic }
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

            Timer {
                id: _showTimer
                interval: widget.toolTipShowDelay
                onTriggered: {
                    if (!_hoverAreaLoader.item || !_hoverAreaLoader.item._showScheduled) return
                    widget.showToolTip()
                    if (widget.toolTipDuration > 0) {
                        _autoHideTimer.interval = widget.toolTipDuration
                        _autoHideTimer.start()
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
    }

    // Hover detection 悬停检测
    Loader {
        id: _hoverAreaLoader
        objectName: "_hoverAreaLoader"
        anchors.fill: parent
        active: widget.toolTipText !== ""

        sourceComponent: MouseArea {
            id: _hoverArea

            // ==================== Internal Props 内部属性 ====================
            property bool _showScheduled: false

            objectName: "_hoverArea"
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
            propagateComposedEvents: true

            onEntered: {
                _showScheduled = true
                if (_toolTipLoader.item) _toolTipLoader.item.startShowTimer()
            }
            onExited: {
                _showScheduled = false
                if (_toolTipLoader.item) {
                    _toolTipLoader.item.stopShowTimer()
                    _toolTipLoader.item.startHideTimer()
                }
            }
        }
    }
}
