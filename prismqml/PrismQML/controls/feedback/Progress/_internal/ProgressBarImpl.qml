// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data"

// ProgressBarImpl - Bar progress implementation 条形进度条实现
// Internal component, use Progress with type_bar 内部组件，使用Progress配合type_bar
Item {
    id: control
    
    // ==================== Required Props 必需属性 ====================
    required property real value
    required property real from
    required property real to
    required property bool indeterminate
    required property bool paused
    required property bool error
    required property bool showText
    required property string text
    required property bool filled  // type_bar_filled 是否填充样式
    
    // ==================== Computed 计算属性 ====================
    readonly property real position: (to > from) ? (value - from) / (to - from) : 0
    readonly property color progressColor: {
        if (error) return Enums.isDark ? Enums.statusLevel.errorColorDark : Enums.statusLevel.errorColor
        if (paused) return Enums.isDark ? Enums.statusLevel.warningColorDark : Enums.statusLevel.warningColor
        return Enums.accentColor
    }
    readonly property color trackColor: Enums.stateColor.progressTrack
    
    // ==================== Viewport Detection 可视区域检测（内联实现）====================
    property Item _flickableAncestor: null
    property bool _isInViewport: true
    
    function _findFlickable() {
        var p = control.parent
        while (p) {
            if (p instanceof Flickable) return p
            p = p.parent
        }
        return null
    }
    
    function _updateViewport() {
        try {
            if (!_flickableAncestor || !control.visible) {
                _isInViewport = control.visible
                return
            }
            // Check if contentItem exists 检查contentItem是否存在
            if (!_flickableAncestor.contentItem) {
                _isInViewport = true
                return
            }
            // Check if height is valid 检查高度是否有效
            if (_flickableAncestor.height <= 0) {
                _isInViewport = true
                return
            }
            var pos = control.mapToItem(_flickableAncestor.contentItem, 0, 0)
            var viewTop = _flickableAncestor.contentY
            var viewBottom = viewTop + _flickableAncestor.height
            var buffer = control.height
            _isInViewport = (pos.y + control.height + buffer > viewTop) && (pos.y - buffer < viewBottom)
        } catch (e) {
            // Fallback to visible if any error occurs 发生任何错误时回退到可见
            _isInViewport = true
        }
    }
    
    Component.onCompleted: {
        _flickableAncestor = _findFlickable()
        if (_flickableAncestor) {
            _flickableAncestor.contentYChanged.connect(_updateViewport)
            _flickableAncestor.heightChanged.connect(_updateViewport)
        }
        _updateViewport()
    }
    
    onVisibleChanged: _updateViewport()
    onYChanged: if (_flickableAncestor) Qt.callLater(_updateViewport)
    
    // ==================== Size 尺寸 ====================
    implicitWidth: 200
    implicitHeight: filled ? 24 : 4
    clip: true
    
    // Track 轨道
    Rectangle {
        anchors.fill: parent
        radius: filled ? Enums.radius.small : (height / 2)
        color: control.trackColor
        // neo: 轨道加黑边(白轨道靠黑边显形)
        border.width: Enums.isNeobrutalism ? Enums.border.medium : 0
        border.color: Enums.isNeobrutalism ? Enums.stateColor.border : Enums.transparent
    }
    
    // Progress 进度
    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: parent.width * control.position
        radius: filled ? Enums.radius.small : (height / 2)
        color: control.progressColor
        visible: !control.indeterminate
        Behavior on width { NumberAnimation { duration: Enums.duration.fast } }
    }
    
    // Filled text 填充文字
    Label {
        anchors.centerIn: parent
        text: control.text !== "" ? control.text : Math.round(control.position * 100) + "%"
        type: Enums.label.type_caption
        color: control.position > 0.5 ? "white" : (Enums.isDark ? "white" : "black")
        visible: control.filled && control.showText && !control.indeterminate
    }
    
    // ==================== Indeterminate 不确定进度(单块加速穿梭) ====================
    IndeterminateBarImpl {
        anchors.fill: parent
        visible: control.indeterminate
        color: control.progressColor
        radius: filled ? Enums.radius.small : (height / 2)
        running: control.indeterminate && control._isInViewport && control.visible
    }
}
