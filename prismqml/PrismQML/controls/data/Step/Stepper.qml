// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../data"
import "../../../effects"

// Stepper - Fluent Design step progress bar 步骤进度条
// Features: icon support, animated progress line, and clickable steps 特性：图标、进度线动画与可点击步骤
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    // Steps format: [{text, icon}, ...] or ["text1", "text2", ...] 步骤格式支持对象或文本数组
    property var steps: []
    property int currentStep: 0
    property int indicatorSize: 36  // Circle size 圆形大小
    
    // ==================== Readonly State 只读状态 ====================
    readonly property real _stepWidth: _safeSteps.length > 0 ? width / _safeSteps.length : 0
    readonly property real _lineStartX: _stepWidth / 2  // First circle center 第一个圆圈中心
    readonly property real _lineEndX: width - _stepWidth / 2  // Last circle center 最后一个圆圈中心
    readonly property real _lineWidth: _lineEndX - _lineStartX  // Total line width 总线宽
    readonly property color _stepLineColor: Enums.stateColor.border
    readonly property color _stepActiveColor: Enums.accentColor
    readonly property color _stepInactiveColor: Enums.cardColor
    readonly property color _stepBorderColor: Enums.stateColor.border
    readonly property color _stepActiveContentColor: Enums.accentForeground
    readonly property color _stepInactiveContentColor: Enums.textColor.secondary
    readonly property color _stepActiveLabelColor: Enums.textColor.primary
    readonly property var _safeSteps: _listOrEmpty(steps)
    readonly property int _safeCurrentStep: _safeSteps.length > 0
        ? Math.max(0, Math.min(currentStep, _safeSteps.length - 1)) : 0

    // ==================== Signals 信号 ====================
    signal stepChanged(int step)
    signal stepClicked(int index)
    
    // ==================== Public Methods 公开方法 ====================
    function stepNext() { if (_safeCurrentStep < _safeSteps.length - 1) currentStep = _safeCurrentStep + 1 }
    function stepBack() { if (_safeCurrentStep > 0) currentStep = _safeCurrentStep - 1 }

    // ==================== Internal Methods 内部方法 ====================
    function _listOrEmpty(value) {
        return value && typeof value.length === "number" ? value : []
    }

    function _getStepText(step) { return typeof step === "string" ? step : (step && step.text || "") }
    function _getStepIcon(step) { return typeof step === "string" ? "" : (step && step.icon || "") }
    
    // ==================== Size 尺寸 ====================
    onCurrentStepChanged: stepChanged(currentStep)
    implicitWidth: Math.max(400, _safeSteps.length * 100)
    implicitHeight: indicatorSize + Enums.spacing.m + Enums.typography.caption + Enums.spacing.s

    // ==================== Content 内容 ====================
    // Background line 背景连接线
    Rectangle {
        x: _lineStartX
        y: indicatorSize / 2 - Enums.border.normal / 2
        width: _lineWidth
        height: Enums.border.normal
        color: control._stepLineColor
        visible: control._safeSteps.length > 1
    }
    
    // Progress line 进度连接线
    Rectangle {
        x: _lineStartX
        y: indicatorSize / 2 - Enums.border.normal / 2
        width: control._safeSteps.length > 1
               ? _lineWidth * control._safeCurrentStep / (control._safeSteps.length - 1) : 0
        height: Enums.border.normal
        color: control._stepActiveColor
        visible: control._safeSteps.length > 1
        
        Behavior on width { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic } }
    }
    
    // Step indicators 步骤指示器
    Row {
        anchors.fill: parent
        
        Repeater {
            model: control._safeSteps
            
            Item {
                readonly property bool isCompleted: index < control._safeCurrentStep
                readonly property bool isCurrent: index === control._safeCurrentStep
                readonly property bool isActive: index <= control._safeCurrentStep
                readonly property string stepIcon: control._getStepIcon(modelData)

                width: parent.width / Math.max(1, control._safeSteps.length)
                height: parent.height
                
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
                            color: isActive ? control._stepActiveColor : control._stepInactiveColor
                            border.width: isActive ? 0 : Enums.border.normal
                            border.color: control._stepBorderColor

                            // Trigger bounce when becoming active 激活时触发弹跳
                            onColorChanged: if (isActive) bounceAnim.start()
                            
                            Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                            Behavior on border.width { NumberAnimation { duration: Enums.duration.fast } }
                            
                            // Bounce animation when step changes 步骤切换弹跳动画
                            SequentialAnimation {
                                id: bounceAnim
                                NumberAnimation { target: indicator; property: "scale"; to: 1.2; duration: Enums.duration.fast; easing.type: Easing.OutQuad }
                                NumberAnimation { target: indicator; property: "scale"; to: 1.0; duration: Enums.duration.fast; easing.type: Easing.OutBounce }
                            }
                            
                            // Icon (for completed or has icon) 图标
                            Icon {
                                id: checkIcon
                                anchors.centerIn: parent
                                icon: isCompleted ? Enums.icon.checkmark : stepIcon
                                iconSize: Enums.iconSize.s
                                color: control._stepActiveContentColor
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
                                color: isActive ? control._stepActiveContentColor : control._stepInactiveContentColor
                                visible: !isCompleted && (stepIcon === "" || !isActive)
                                
                                Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                            }
                            
                            // Hover effect 悬停效果
                            MouseArea {
                                id: indicatorArea
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                hoverEnabled: true
                                onClicked: control.stepClicked(index)
                                onEntered: indicator.scale = 1.08
                                onExited: indicator.scale = 1.0
                            }
                            
                            HoverBehavior on scale {
                                active: indicatorArea.containsMouse
                                enterDuration: Enums.duration.fast
                                easingType: Easing.OutQuad
                            }
                        }
                    }
                    
                    // Label 标签
                    Label {
                        anchors.horizontalCenter: parent.horizontalCenter
                        type: Enums.label.type_caption
                        text: control._getStepText(modelData)
                        color: isActive ? control._stepActiveLabelColor : control._stepInactiveContentColor
                        horizontalAlignment: Text.AlignHCenter
                        
                        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
                    }
                }
            }
        }
    }
}
