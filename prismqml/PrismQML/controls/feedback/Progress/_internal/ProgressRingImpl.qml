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
    // Viewport detection lives in ViewportMixin 视口检测由 ViewportMixin 持有
    readonly property bool _isInViewport: viewport.isInViewport

    implicitWidth: Enums.controlSize.progressRingSize
    implicitHeight: Enums.controlSize.progressRingSize

    // ==================== Content 内容 ====================
    ViewportMixin {
        id: viewport
        target: control
    }

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
