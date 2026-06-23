// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
    property color borderColorLight: "transparent"  // Light border color 浅色边框颜色
    property color borderColorDark: "transparent"  // Dark border color 深色边框颜色
    property int iconSize: Enums.iconSize.s  // Icon size 图标尺寸
    
    
    // ==================== Public Methods 公共方法 ====================
    function getText() { return text }


    readonly property color currentColor: {
        switch (status) {
            case Enums.statusLevel.success: return Enums.statusLevel.successColor
            case Enums.statusLevel.warning: return Enums.statusLevel.warningColor
            case Enums.statusLevel.error: return Enums.statusLevel.errorColor
            case Enums.statusLevel.attention: return Enums.statusLevel.attentionColor
            case Enums.statusLevel.processing: return Enums.isDark ? Enums.statusLevel.processingColorDark : Enums.statusLevel.processingColor
            default: return Enums.statusLevel.infoColor
        }
    }
    
    implicitWidth: contentRow.implicitWidth + 16
    implicitHeight: Enums.spacing.xxxl
    radius: Enums.isNeobrutalism ? Enums.neo.radius : Enums.radius.small

    color: Enums.stateColor.accentSubtle
    // neo: 始终黑粗边(标签靠黑边显形); Fluent: 按 showBorder
    border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : (showBorder ? Enums.border.thin : 0)
    border.color: Enums.isNeobrutalism ? Enums.stateColor.border : (Enums.isDark ? borderColorDark : borderColorLight)
    
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
                running: control.status === Enums.statusLevel.processing
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
