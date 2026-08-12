// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../Label"

// Tag - Status tag component 状态标签组件
// Display different status with colored dot and text 显示不同状态（带颜色点和文字）
Rectangle {
    id: control
    
    // Use Enums.statusLevel enum 使用枚举
    property int status: Enums.statusLevel.info
    property string text: ""
    property bool showDot: true
    property bool showBorder: false  // Border visibility 边框可见性
    property color borderColorLight: Enums.transparent  // Light border color 浅色边框颜色
    property color borderColorDark: Enums.transparent  // Dark border color 深色边框颜色
    property int iconSize: Enums.iconSize.s  // Icon size 图标尺寸
    readonly property string _statusKey: {
        switch (status) {
            case Enums.statusLevel.success: return "success"
            case Enums.statusLevel.warning: return "warning"
            case Enums.statusLevel.error: return "error"
            case Enums.statusLevel.attention: return "attention"
            case Enums.statusLevel.processing: return "processing"
            default: return "info"
        }
    }
    readonly property color currentColor: Enums.statusLevel.getColorByLevel(status)
    readonly property int _tagRadius: Enums.surfaceRadius(Enums.radius.small)
    readonly property color _tagBackground: Enums.stateColor.accentSubtle
    readonly property real _tagBorderWidth: Enums.hasOutlinedSurfaces
                                            ? Enums.surfaceBorderWidth(Enums.border.thin)
                                            : (showBorder ? Enums.border.thin : 0)
    readonly property color _tagBorderColor: Enums.hasOutlinedSurfaces
                                              ? Enums.stateColor.border
                                              : (Enums.isDark ? borderColorDark : borderColorLight)

    // ==================== Public Methods 公开方法 ====================
    function getText() { return text }
    
    implicitWidth: contentRow.implicitWidth + 16
    implicitHeight: Enums.spacing.xxxl
    radius: _tagRadius

    color: _tagBackground
    // neo: 始终黑粗边(标签靠黑边显形); Fluent: 按 showBorder
    border.width: _tagBorderWidth
    border.color: _tagBorderColor
    
    Row {
        id: contentRow
        anchors.centerIn: parent
        spacing: Enums.spacing.s
        
        // Status dot 状态点
        Rectangle {
            width: Enums.spacing.s
            height: Enums.spacing.s
            radius: Enums.border.thick  // Circle 圆形
            anchors.verticalCenter: parent.verticalCenter
            color: control.currentColor
            visible: control.showDot
            
            // Processing animation 处理中动画
            SequentialAnimation on opacity {
                running: control.status === Enums.statusLevel.processing &&
                         control.visible
                loops: Animation.Infinite
                NumberAnimation { to: 0.3; duration: Enums.duration.slow * 2 }
                NumberAnimation { to: 1; duration: Enums.duration.slow * 2 }
            }
        }
        
        Label {
            type: Enums.label.type_caption
            text: control.text
            color: control.currentColor
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
