// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data/Label"

// ProgressRingImpl - Ring progress implementation 环形进度条实现
Item {
    id: control
    
    required property real value
    required property real from
    required property real to
    required property bool indeterminate
    required property bool running
    required property int strokeWidth
    required property bool showText
    required property string text
    
    readonly property real position: (to > from) ? (value - from) / (to - from) : 0
    readonly property color progressColor: Enums.accentColor
    readonly property color trackColor: Enums.stateColor.border
    
    implicitWidth: Enums.controlSize.progressRingSize
    implicitHeight: Enums.controlSize.progressRingSize
    
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
    
    // Track ring 轨道环
    Canvas {
        id: trackCanvas
        anchors.fill: parent
        visible: !control.indeterminate
        onPaint: {
            var ctx = getContext("2d"); ctx.reset()
            var cx = width / 2, cy = height / 2, r = Math.min(cx, cy) - control.strokeWidth / 2
            ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2)
            ctx.strokeStyle = control.trackColor; ctx.lineWidth = control.strokeWidth; ctx.stroke()
        }
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        Component.onCompleted: requestPaint()
        Connections { target: ThemeManager; function onThemeChanged() { trackCanvas.requestPaint() } }
    }
    
    // Progress ring 进度环
    Canvas {
        id: progressCanvas
        anchors.fill: parent; rotation: -90; visible: !control.indeterminate
        onPaint: {
            var ctx = getContext("2d"); ctx.reset()
            var cx = width / 2, cy = height / 2, r = Math.min(cx, cy) - control.strokeWidth / 2
            if (control.position > 0) {
                ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2 * control.position)
                ctx.strokeStyle = control.progressColor; ctx.lineCap = "round"; ctx.lineWidth = control.strokeWidth; ctx.stroke()
            }
        }
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        Connections { target: control; function onValueChanged() { progressCanvas.requestPaint() } }
        Connections { target: control; function onPositionChanged() { progressCanvas.requestPaint() } }
        Connections { target: ThemeManager; function onThemeChanged() { progressCanvas.requestPaint() } }
        Component.onCompleted: requestPaint()
    }
    
    // Indeterminate ring 不确定进度环(伸缩弧脉动)
    IndeterminateArcImpl {
        anchors.fill: parent
        visible: control.indeterminate
        running: control.indeterminate && control.running && control.visible && control._isInViewport
        color: control.progressColor
        strokeWidth: control.strokeWidth
    }
    
    // Center text 中心文本
    Label {
        type: Enums.label.type_caption
        anchors.centerIn: parent
        text: control.text !== "" ? control.text : Math.round(control.position * 100) + "%"
        font.pixelSize: Math.max(Enums.typography.caption, parent.width / 5)
        color: Enums.foregroundColor
        visible: control.showText && !control.indeterminate
    }
}
