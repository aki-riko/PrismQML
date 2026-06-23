// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../data"

// Stepper - Fluent Design step progress bar 步骤进度条
// Features 特性: icon support, animated progress line, clickable steps
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    // Steps format: [{text, icon}, ...] or ["text1", "text2", ...]
    property var steps: []
    property int currentStep: 0
    property int indicatorSize: 36  // Circle size 圆形大小
    
    // ==================== Signals 信号 ====================
    signal stepChanged(int step)
    signal stepClicked(int index)
    
    // ==================== Methods 方法 ====================
    function stepNext() { if (currentStep < steps.length - 1) currentStep++ }
    function stepBack() { if (currentStep > 0) currentStep-- }
    
    onCurrentStepChanged: stepChanged(currentStep)
    
    implicitWidth: Math.max(400, steps.length * 100)
    implicitHeight: indicatorSize + Enums.spacing.m + Enums.typography.caption + Enums.spacing.s
    
    // ==================== Helper 辅助函数 ====================
    function _getStepText(step) { return typeof step === "string" ? step : (step.text || "") }
    function _getStepIcon(step) { return typeof step === "string" ? "" : (step.icon || "") }
    
    // Line position calculation 连接线位置计算
    readonly property real _stepWidth: steps.length > 0 ? width / steps.length : 0
    readonly property real _lineStartX: _stepWidth / 2  // First circle center 第一个圆圈中心
    readonly property real _lineEndX: width - _stepWidth / 2  // Last circle center 最后一个圆圈中心
    readonly property real _lineWidth: _lineEndX - _lineStartX  // Total line width 总线宽
    
    // ==================== Background Line 背景连接线 ====================
    Rectangle {
        x: _lineStartX
        y: indicatorSize / 2 - Enums.border.normal / 2
        width: _lineWidth
        height: Enums.border.normal
        color: Enums.stateColor.border
        visible: steps.length > 1
    }
    
    // ==================== Progress Line 进度连接线 ====================
    Rectangle {
        x: _lineStartX
        y: indicatorSize / 2 - Enums.border.normal / 2
        width: steps.length > 1 ? _lineWidth * currentStep / (steps.length - 1) : 0
        height: Enums.border.normal
        color: Enums.accentColor
        visible: steps.length > 1
        
        Behavior on width { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic } }
    }
    
    // ==================== Step Indicators 步骤指示器 ====================
    Row {
        anchors.fill: parent
        
        Repeater {
            model: steps
            
            Item {
                width: parent.width / steps.length
                height: parent.height
                
                readonly property bool isCompleted: index < currentStep
                readonly property bool isCurrent: index === currentStep
                readonly property bool isActive: index <= currentStep
                readonly property string stepIcon: control._getStepIcon(modelData)
                
                Column {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: Enums.spacing.m
                    
                    // Circle indicator 圆形指示器
                    Item {
                        id: indicatorContainer
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: indicatorSize
                        height: indicatorSize
                        
                        Rectangle {
                            id: indicator
                            anchors.centerIn: parent
                            width: indicatorSize
                            height: indicatorSize
                            radius: indicatorSize / 2
                            color: isActive ? Enums.accentColor : Enums.cardColor
                            border.width: isActive ? 0 : Enums.border.normal
                            border.color: Enums.stateColor.border
                            
                            Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                            Behavior on border.width { NumberAnimation { duration: Enums.duration.fast } }
                            
                            // Bounce animation when step changes 步骤切换弹跳动画
                            SequentialAnimation {
                                id: bounceAnim
                                NumberAnimation { target: indicator; property: "scale"; to: 1.2; duration: Enums.duration.fast; easing.type: Easing.OutQuad }
                                NumberAnimation { target: indicator; property: "scale"; to: 1.0; duration: Enums.duration.fast; easing.type: Easing.OutBounce }
                            }
                            
                            // Trigger bounce when becoming active 激活时触发弹跳
                            onColorChanged: if (isActive) bounceAnim.start()
                            
                            // Icon (for completed or has icon) 图标
                            Icon {
                                id: checkIcon
                                anchors.centerIn: parent
                                icon: isCompleted ? Enums.icon.checkmark : stepIcon
                                iconSize: Enums.iconSize.s
                                color: "white"
                                visible: isCompleted || (isActive && stepIcon !== "")
                                opacity: 0
                                scale: 0.5
                                
                                // Fade in animation 淡入动画
                                states: State {
                                    name: "visible"
                                    when: isCompleted || (isActive && stepIcon !== "")
                                    PropertyChanges { target: checkIcon; opacity: 1; scale: 1.0 }
                                }
                                
                                transitions: Transition {
                                    to: "visible"
                                    ParallelAnimation {
                                        NumberAnimation { property: "opacity"; duration: Enums.duration.fast; easing.type: Easing.OutQuad }
                                        NumberAnimation { property: "scale"; duration: Enums.duration.medium; easing.type: Easing.OutBack }
                                    }
                                }
                            }
                            
                            // Number (for pending or current without icon) 数字
                            Label {
                                id: numberText
                                anchors.centerIn: parent
                                type: Enums.label.type_body
                                text: String(index + 1)
                                color: isActive ? "white" : Enums.secondaryForeground
                                visible: !isCompleted && (stepIcon === "" || !isActive)
                                
                                Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                            }
                            
                            // Hover effect 悬停效果
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                hoverEnabled: true
                                onClicked: control.stepClicked(index)
                                onEntered: indicator.scale = 1.08
                                onExited: indicator.scale = 1.0
                            }
                            
                            Behavior on scale { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutQuad } }
                        }
                    }
                    
                    // Label 标签
                    Label {
                        anchors.horizontalCenter: parent.horizontalCenter
                        type: Enums.label.type_caption
                        text: control._getStepText(modelData)
                        color: isActive ? Enums.foregroundColor : Enums.secondaryForeground
                        horizontalAlignment: Text.AlignHCenter
                        
                        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                    }
                }
            }
        }
    }
}
