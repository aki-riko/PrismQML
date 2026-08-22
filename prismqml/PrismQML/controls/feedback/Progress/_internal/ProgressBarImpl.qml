// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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
    
    // ==================== Readonly State 只读状态 ====================
    readonly property real position: (to > from) ? (value - from) / (to - from) : 0
    readonly property color progressColor: {
        if (error) return Enums.isDark ? Enums.statusLevel.errorColorDark : Enums.statusLevel.errorColor
        if (paused) return Enums.isDark ? Enums.statusLevel.warningColorDark : Enums.statusLevel.warningColor
        return Enums.accentColor
    }
    readonly property color trackColor: Enums.stateColor.progressTrack
    readonly property real _barRadius: filled ? (Enums.radius.small) : (height / 2)
    readonly property color _filledTextColor: control.position > 0.5 ? Enums.accentForeground : Enums.textColor.primary
    
    // ==================== Internal Props 内部属性 ====================
    // Viewport detection lives in ViewportMixin 视口检测由 ViewportMixin 持有
    readonly property bool _isInViewport: viewport.isInViewport

    // ==================== Size 尺寸 ====================
    implicitWidth: 200
    implicitHeight: filled ? 24 : 4
    clip: true

    // ==================== Content 内容 ====================
    ViewportMixin {
        id: viewport
        target: control
    }

    // Track 轨道
    Rectangle {
        anchors.fill: parent
        radius: Enums.isVintageTicket ? Enums.ticket.radius : control._barRadius
        color: control.trackColor
        // neo: 轨道加黑边(白轨道靠黑边显形)
        border.width: Enums.hasOutlinedSurfaces ? Enums.surfaceBorderWidth(Enums.border.thin) : 0
        border.color: Enums.hasOutlinedSurfaces ? Enums.stateColor.border : Enums.transparent
    }
    
    // Progress 进度
    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: parent.width * control.position
        radius: Enums.isVintageTicket ? Enums.ticket.radius : control._barRadius
        color: control.progressColor
        visible: !control.indeterminate
        Behavior on width { NumberAnimation { duration: Enums.duration.fast } }
    }
    
    // Filled text 填充文字
    Label {
        anchors.centerIn: parent
        text: control.text !== "" ? control.text : Math.round(control.position * 100) + "%"
        type: Enums.label.type_caption
        color: control._filledTextColor
        visible: control.filled && control.showText && !control.indeterminate
    }
    
    // Indeterminate moving block 不确定进度单块穿梭
    Loader {
        anchors.fill: parent
        active: control.indeterminate
        sourceComponent: IndeterminateBarImpl {
            color: control.progressColor
            radius: Enums.isVintageTicket ? Enums.ticket.radius : control._barRadius
            running: control.indeterminate && control._isInViewport && control.visible
        }
    }
}
