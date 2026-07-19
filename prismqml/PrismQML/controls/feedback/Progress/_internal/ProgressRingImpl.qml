// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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
    readonly property color progressColor: progressRing.progressColor
    readonly property color trackColor: progressRing.trackColor
    
    // ==================== Internal Props 内部属性 ====================
    // Viewport detection 可视区域检测
    property Item _flickableAncestor: null
    property bool _isInViewport: true
    
    // ==================== Internal Methods 内部方法 ====================
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

    implicitWidth: Enums.controlSize.progressRingSize
    implicitHeight: Enums.controlSize.progressRingSize
    
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
    
    // Standard progress ring 标准进度环
    ProgressRing {
        id: progressRing
        anchors.fill: parent
        value: control.value
        from: control.from
        to: control.to
        indeterminate: control.indeterminate
        paused: !control.running || !control.visible || !control._isInViewport
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
