// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../.."
import "../icons"
import "../../effects"
import "../feedback"
import "../data"
import "../dialogs"

// ProgressDialog - Progress dialog 进度对话框
// Inherits from OverlayDialogCore for mask layer reuse 继承自OverlayDialogCore以复用遮罩层
// Horizontal layout: progress ring on left, text on right 水平布局：左边进度环，右边文字

OverlayDialogCore {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string title: ""
    property string content: ""
    property int ringSize: 64
    property int ringStrokeWidth: Enums.controlSize.progressStrokeWidth
    property int maxWaitingTime: -1  // -1 = infinite wait 无限等待
    property real progress: -1  // -1 = 不确定(转圈), 0~100 = 确定进度百分比
    
    // ==================== Signals 信号 ====================
    signal timeout()
    
    // ==================== Shadow Layer 阴影层 ====================
    // Fluent: 模糊阴影; neo: 硬阴影
    RectangularShadow {
        anchors.fill: container
        radius: container.radius
        color: Enums.shadow.level8.color
        blur: Enums.shadow.level8.blur
        offset: Qt.vector2d(0, Enums.shadow.level8.offset)
        visible: !Enums.isNeobrutalism
    }

    NeoShadow {
        target: container
        visible: Enums.isNeobrutalism
        z: container.z - 1
    }

    // ==================== Main Container 主容器 ====================
    Rectangle {
        id: container
        anchors.centerIn: parent
        width: Math.max(288, contentRow.implicitWidth + 56)
        height: Math.max(110, contentRow.implicitHeight + 40)
        radius: Enums.radius.large
        color: Enums.cardColor
        border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
        border.color: Enums.stateColor.dialogBorder
        
        // Animation 动画
        scale: control._isOpen ? 1 : 0.9
        opacity: control._isOpen ? 1 : 0
        
        Behavior on scale { 
            NumberAnimation { 
                duration: Enums.duration.medium
                easing.type: control._isClosing ? Easing.InBack : Easing.OutBack
            } 
        }
        Behavior on opacity { 
            NumberAnimation { 
                duration: Enums.duration.medium
                onRunningChanged: {
                    if (!running && control._isClosing) {
                        control._isClosing = false
                    }
                }
            } 
        }
        
        // Content - Horizontal layout 内容-水平布局
        Row {
            id: contentRow
            anchors.centerIn: parent
            spacing: Enums.spacing.xxxl
            
            // Progress ring 进度环
            ProgressRing {
                id: progressRing
                width: control.ringSize
                height: control.ringSize
                strokeWidth: control.ringStrokeWidth
                // progress < 0 时不确定(转圈), 否则按 0~100 显示确定进度
                indeterminate: control.progress < 0
                value: control.progress < 0 ? 0 : control.progress
                from: 0
                to: 100
                anchors.verticalCenter: parent.verticalCenter
            }
            
            // Text column 文字列
            Column {
                anchors.verticalCenter: parent.verticalCenter
                spacing: Enums.spacing.s
                
                // Title 标题 - 20px bold
                Label {
                    text: control.title
                    type: Enums.label.type_subtitle
                    color: Enums.textColor.primary
                    visible: text !== ""
                }
                
                // Content 内容 - 14px accent color
                Label {
                    text: control.content
                    type: Enums.label.type_body
                    color: Enums.accentColor  // 主题色
                    wrapMode: Text.WordWrap
                    width: Math.min(implicitWidth, 300)
                    visible: text !== ""
                }
            }
        }
    }
    
    // ==================== Timeout Timer 超时定时器 ====================

    Timer {
        id: timeoutTimer
        interval: control.maxWaitingTime
        running: control._isOpen && control.maxWaitingTime > 0
        onTriggered: {
            control.timeout()
            control.close()
        }
    }
    
    // ==================== Fluent Design兼容方法 ====================
    
    
}
