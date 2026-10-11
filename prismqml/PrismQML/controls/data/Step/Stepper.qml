// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../data"
import "../../utils"
import "../../../effects"
import "_internal"

// Stepper - Fluent Design step progress bar 步骤进度条
// Showcase build: faded rail with a looping highlight sweep, a dot trail flowing
// towards the pending end, a breathing halo plus activation ripple on the current
// step, a completion burst, and an elastic advance with a subtle 3D tilt on every
// step change. Icon support and clickable steps are unchanged.
// 炫技版：两端淡出的底轨叠加循环流光、流向未完成端的点阵、当前步骤的呼吸光晕与激活
// 涟漪、完成迸发，以及每次切换步骤时的弹性推进与轻微 3D 倾斜。图标与可点击步骤保持不变。
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
    readonly property color _stepActiveHighlightColor: Enums.accentColorLight
    readonly property color _stepInactiveColor: Enums.cardColor
    readonly property color _stepBorderColor: Enums.stateColor.border
    readonly property color _stepActiveContentColor: Enums.accentForeground
    readonly property color _stepInactiveContentColor: Enums.textColor.secondary
    readonly property color _stepActiveLabelColor: Enums.textColor.primary
    readonly property var _safeSteps: _listOrEmpty(steps)
    readonly property int _safeCurrentStep: _safeSteps.length > 0
        ? Math.max(0, Math.min(currentStep, _safeSteps.length - 1)) : 0
    readonly property real _connectorProgress: _safeSteps.length > 1
        ? _safeCurrentStep / (_safeSteps.length - 1) : 0
    // Elastic advance geometry shared by the lift and the tilt 弹性推进共用的抬升与倾角
    readonly property real _advanceLift: Enums.spacing.xxs
    readonly property real _tiltPeak: Enums.stepper.tiltPeak
    // Rail thickness tracks the indicator scale: a hairline rail under a large
    // indicator reads as a gap between the steps rather than a connector.
    // 轨道粗细跟随指示器尺度：大圆点下的发丝细线读起来像步骤之间的断裂，而不是连接线。
    readonly property real _railThickness: Math.max(Enums.border.thick,
        indicatorSize * Enums.stepper.railThicknessRatio)
    // Completed steps keep a faint glow so the walked path stays lit
    // 已完成步骤保留一层微光，让走过的路径保持发亮
    readonly property real _completedGlowScale: Enums.stepper.completedGlowScale
    readonly property real _completedGlowOpacity: Enums.opacityLevel.faint

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
    onCurrentStepChanged: {
        stepChanged(currentStep)
        advanceAnim.restart()
    }
    implicitWidth: Math.max(400, _safeSteps.length * 100)
    implicitHeight: indicatorSize + Enums.spacing.m + Enums.typography.caption + Enums.spacing.s

    // ==================== Content 内容 ====================
    // A stepper is a grouped progress indicator; its name is derived from the step
    // numbers the user already sees, so it needs no catalogue entry.
    // 步骤条是分组的进度指示；名称由用户已看到的步数派生，因此无需翻译词条。
    A11ySurface {
        target: control
        role: Enums.accessibility.role_group
        name: String(control.currentStep + 1) + " / " + String(control._safeSteps.length)
    }

    // Showcase motion tokens 炫技动效令牌
    StepperMotion {
        id: motion
    }

    // Elastic advance and 3D tilt container 弹性推进与 3D 倾斜容器
    Item {
        id: tiltLayer

        anchors.fill: parent
        transform: [
            Translate {
                id: advanceLift

                y: 0
            },
            Rotation {
                id: tiltRotation

                origin.x: tiltLayer.width / 2
                origin.y: tiltLayer.height / 2
                axis { x: 1; y: 0; z: 0 }
                angle: 0
            }
        ]

        // Connector layers 连接线图层
        StepperTrack {
            id: track

            x: 0
            y: control.indicatorSize / 2 - control._railThickness / 2
            width: control.width
            height: control._railThickness
            lineStartX: control._lineStartX
            lineWidth: control._lineWidth
            thickness: control._railThickness
            progress: control._connectorProgress
            railColor: control._stepLineColor
            progressColor: control._stepActiveColor
            highlightColor: control._stepActiveHighlightColor
            animated: motion.animated
            growDuration: motion.grow
            sweepDuration: motion.sweep
            flowDuration: motion.flow
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
                    // Touch has no hover preview: on touch the hover treatment follows the press
                    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
                    readonly property bool _touchActive: Touch.feedback(indicatorArea.containsMouse,
                                                                       indicatorArea.pressed)
                    // Burst only on a real advance. The first binding pass resolves
                    // isCompleted from false to true for steps the user never walked, and
                    // celebrating those would both lie and fire several bursts at load.
                    // 仅在真实推进时迸发。首次绑定求值会把用户并未走过的步骤从 false 解析为
                    // true，庆祝它们既与事实不符，又会在加载时同时触发多组迸发。
                    property bool _burstArmed: false

                    width: parent.width / Math.max(1, control._safeSteps.length)
                    height: parent.height

                    Component.onCompleted: _burstArmed = true
                    // Celebrate the step the user just completed 庆祝刚刚完成的步骤
                    onIsCompletedChanged: if (isCompleted && _burstArmed) burst.burst()

                    Column {
                        anchors.horizontalCenter: parent.horizontalCenter
                        spacing: Enums.spacing.m

                        // Circle indicator 圆形指示器
                        Item {
                            id: indicatorContainer
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: indicatorSize
                            height: indicatorSize

                            // Breathing halo and activation ripple 呼吸光晕与激活涟漪
                            StepperHalo {
                                id: halo

                                anchors.centerIn: parent
                                diameter: control.indicatorSize
                                haloColor: control._stepActiveColor
                                animated: motion.animated
                                breatheDuration: motion.breathe
                                rippleDuration: motion.ripple
                                active: isCurrent
                            }

                            // Completion burst ring and particles 完成迸发光环与粒子
                            StepperBurst {
                                id: burst

                                anchors.centerIn: parent
                                diameter: control.indicatorSize
                                ringColor: control._stepActiveHighlightColor
                                particleColor: control._stepActiveColor
                                animated: motion.animated
                                duration: motion.burst
                                z: Enums.zIndex.content
                            }

                            // Completed step glow 完成节点微光
                            Rectangle {
                                id: completedGlow

                                anchors.centerIn: parent
                                width: control.indicatorSize * control._completedGlowScale
                                height: width
                                radius: width / 2
                                color: control._stepActiveColor
                                opacity: isCompleted ? control._completedGlowOpacity : Enums.opacityLevel.invisible
                                visible: opacity > Enums.opacityLevel.invisible

                                Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
                            }

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
                                    // Single source for the hover/press scale and its reset
                                    // 悬停/按压缩放与其复位值的唯一来源
                                    readonly property real _hoverScale: Enums.stepper.hoverScale
                                    readonly property real _restScale: Enums.stepper.baseScale

                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    hoverEnabled: true
                                    onClicked: control.stepClicked(index)
                                    onEntered: indicator.scale = indicatorArea._hoverScale
                                    onExited: indicator.scale = indicatorArea._restScale
                                    // Touch has no hover preview: the same scale follows the press
                                    // and resets on release, since touch never emits an exit
                                    // 触摸没有 hover 预览: 同一缩放改为跟随按压并在松手复位,
                                    // 因为触摸端不会派发 exit
                                    onPressedChanged: if (Touch.isTouch)
                                                          indicator.scale = indicatorArea.pressed
                                                              ? indicatorArea._hoverScale
                                                              : indicatorArea._restScale
                                }

                                HoverBehavior on scale {
                                    active: _touchActive
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

    // Elastic advance on step change 步骤切换时的弹性推进
    SequentialAnimation {
        id: advanceAnim

        NumberAnimation { target: advanceLift; property: "y"; from: 0; to: -control._advanceLift; duration: motion.advance; easing.type: Easing.OutCubic }
        NumberAnimation { target: tiltRotation; property: "angle"; from: 0; to: -control._tiltPeak; duration: motion.advance; easing.type: Easing.OutCubic }
        ParallelAnimation {
            NumberAnimation { target: advanceLift; property: "y"; from: -control._advanceLift; to: 0; duration: motion.advance; easing.type: Easing.OutBack }
            NumberAnimation { target: tiltRotation; property: "angle"; from: -control._tiltPeak; to: 0; duration: motion.advance; easing.type: Easing.OutBack }
        }
    }
}
