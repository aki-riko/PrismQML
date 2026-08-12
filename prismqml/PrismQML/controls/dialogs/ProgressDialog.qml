// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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

    // ==================== Readonly State 只读状态 ====================
    readonly property real _progressMinimum: 0
    readonly property real _progressMaximum: 100
    readonly property bool _isIndeterminate: progress < _progressMinimum
    readonly property bool _progressComplete:
        !_isIndeterminate && progress >= _progressMaximum

    readonly property int _dialogRadius: Enums.surfaceRadius(Enums.radius.large)
    readonly property color _dialogBackground: Enums.cardColor
    readonly property real _dialogBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color _dialogBorderColor: Enums.stateColor.dialogBorder
    readonly property color _dialogShadowColor: Enums.shadow.level16.color
    readonly property real _dialogShadowBlur: Enums.shadow.level16.blur
    readonly property real _dialogShadowOffset: Enums.shadow.level16.offset
    
    // ==================== Signals 信号 ====================
    signal timeout()
    
    // ==================== Content 内容 ====================
    // Fluent: 模糊阴影; neo: 硬阴影
    RectangularShadow {
        anchors.fill: container
        radius: container.radius
        color: control._dialogShadowColor
        blur: control._dialogShadowBlur
        offset.x: 0
        offset.y: control._dialogShadowOffset
        visible: Enums.usesSoftElevation
    }

    NeoShadow {
        target: container
        visible: Enums.isNeobrutalism
        z: container.z - 1
    }

    // Main container 主容器
    Rectangle {
        id: container
        anchors.centerIn: parent
        width: Math.max(288, contentRow.implicitWidth + 56)
        height: Math.max(110, contentRow.implicitHeight + 40)
        radius: control._dialogRadius
        color: control._dialogBackground
        border.width: control._dialogBorderWidth
        border.color: control._dialogBorderColor
        // Animation 动画
        scale: control._isOpen ? 1 : 0.9
        opacity: control._isOpen ? 1 : 0

        TicketPaper {
            anchors.fill: parent
        }
        
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
            
            // Progress indicator 进度指示器
            Item {
                id: progressIndicator

                width: control.ringSize
                height: control.ringSize
                anchors.verticalCenter: parent.verticalCenter

                ProgressRing {
                    id: progressRing

                    anchors.fill: parent
                    strokeWidth: control.ringStrokeWidth
                    // Negative progress is indeterminate; otherwise use the bounded range.
                    // 负进度表示不确定状态，否则使用固定百分比范围。
                    indeterminate: control._isIndeterminate
                    value: control._isIndeterminate
                        ? control._progressMinimum
                        : control.progress
                    from: control._progressMinimum
                    to: control._progressMaximum
                }

                Icon {
                    objectName: "progressDialogCompletionIcon"
                    anchors.centerIn: parent
                    iconSize: Enums.iconSize.xxl
                    icon: control._progressComplete ? Enums.icon.checkmark : ""
                    color: progressRing.progressColor
                    visible: control._progressComplete
                }
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
    
    // Timeout timer 超时定时器

    Timer {
        id: timeoutTimer
        interval: control.maxWaitingTime
        running: control._isOpen && control.maxWaitingTime > 0
        onTriggered: {
            control.timeout()
            control.close()
        }
    }
    
}
