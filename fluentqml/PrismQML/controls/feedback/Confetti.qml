// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."

// Confetti - Pure QtQuick implementation 彩纸动画
// Celebration/success confetti falling effect 庆祝彩纸飘落效果
Item {
    id: control
    
    // Public properties 公开属性

    property bool running: false
    property int particleCount: 150
    property int duration: Enums.duration.confetti
    
    // Fluent风格的柔和色彩 Fluent-style soft colors
    property var colors: [
        Enums.accentColor,
        Qt.lighter(Enums.accentColor, 1.3),
        Qt.darker(Enums.accentColor, 1.2)
    ].concat(Enums.confettiColors.palette)
    
    anchors.fill: parent
    z: Enums.zIndex.overlay
    
    // Internal state 内部状态

    property int _spawnIndex: 0
    
    // Spawn initial batch immediately 立即生成首批粒子
    function _spawnBatch(count) {
        for (var i = 0; i < count && _spawnIndex < particleCount; i++) {
            particleComponent.createObject(control)
            _spawnIndex++
        }
    }

    // ==================== Public Methods 公共方法 ====================


    // Start confetti effect 启动彩纸效果

    function start() {
        running = false
        _spawnIndex = 0
        running = true
        _spawnBatch(20)  // Spawn initial batch immediately 立即生成首批粒子

    }

    // Stop confetti effect 停止彩纸效果

    function stop() {
        running = false
    }

    // Particle spawn timer 粒子生成定时器

    Timer {
        id: spawnTimer
        interval: 5
        repeat: true
        running: control.running && _spawnIndex < particleCount
        onTriggered: _spawnBatch(8)
    }
    
    // Auto-stop timer 自动停止定时器

    Timer {
        id: stopTimer
        interval: control.duration + Enums.duration.dialog
        running: control.running
        onTriggered: control.running = false
    }
    
    onRunningChanged: {
        if (running) {
            _spawnIndex = 0
        }
    }
    
    // Particle component 粒子组件

    Component {
        id: particleComponent
        
        Item {
            id: particle
            
            // Random initial position (full width coverage) 随机初始位置（覆盖整个宽度）

            x: Math.random() * control.width
            y: -30
            
            // Random properties 随机属性

            property real targetX: x + (Math.random() - 0.5) * control.width * 0.3
            property real targetY: control.height + 50
            property real fallDuration: control.duration * (0.7 + Math.random() * 0.6)
            property int shapeType: Math.floor(Math.random() * 3)
            property color particleColor: control.colors[Math.floor(Math.random() * control.colors.length)]
            property real particleSize: Enums.spacing.m + Math.random() * Enums.spacing.m
            property real initialRotation: Math.random() * 360
            property real rotationSpeed: (Math.random() - 0.5) * 720
            property real swayAmount: Enums.spacing.xl + Math.random() * Enums.spacing.xl  // Sway amount 轻微摆动幅度

            
            // Shape rendering 形状渲染

            Loader {
                anchors.centerIn: parent
                sourceComponent: {
                    switch (particle.shapeType) {
                        case 0: return rectShape      // Rectangle 矩形

                        case 1: return circleShape    // Circle 圆形

                        case 2: return ribbonShape    // Ribbon 丝带

                    }
                }
            }
            
            // Rectangle confetti 矩形彩纸

            Component {
                id: rectShape
                Rectangle {
                    width: particle.particleSize
                    height: particle.particleSize * 0.6
                    radius: Enums.radius.micro
                    color: particle.particleColor
                    rotation: particle.initialRotation
                    
                    RotationAnimation on rotation {
                        from: particle.initialRotation
                        to: particle.initialRotation + particle.rotationSpeed
                        duration: particle.fallDuration
                        running: true
                    }
                }
            }
            
            // Circle confetti 圆形彩纸

            Component {
                id: circleShape
                Rectangle {
                    width: particle.particleSize * 0.8
                    height: width
                    radius: width / 2
                    color: particle.particleColor
                }
            }
            
            // Ribbon confetti 丝带彩纸

            Component {
                id: ribbonShape
                Rectangle {
                    width: particle.particleSize * 1.5
                    height: particle.particleSize * 0.3
                    radius: height / 2
                    color: particle.particleColor
                    rotation: particle.initialRotation
                    
                    RotationAnimation on rotation {
                        from: particle.initialRotation
                        to: particle.initialRotation + particle.rotationSpeed * 1.5
                        duration: particle.fallDuration
                        running: true
                    }
                }
            }
            
            // Falling animation 飘落动画

            ParallelAnimation {
                id: fallAnimation
                running: true
                
                // Vertical fall with gravity feel 垂直下落（带重力感）

                NumberAnimation {
                    target: particle
                    property: "y"
                    to: particle.targetY
                    duration: particle.fallDuration
                    easing.type: Easing.InQuad
                }
                
                // Horizontal drift with gentle sway 水平漂移（带轻微摆动）

                SequentialAnimation {
                    NumberAnimation {
                        target: particle
                        property: "x"
                        to: particle.targetX + particle.swayAmount
                        duration: particle.fallDuration * 0.3
                        easing.type: Easing.OutSine
                    }
                    NumberAnimation {
                        target: particle
                        property: "x"
                        to: particle.targetX - particle.swayAmount * 0.5
                        duration: particle.fallDuration * 0.4
                        easing.type: Easing.InOutSine
                    }
                    NumberAnimation {
                        target: particle
                        property: "x"
                        to: particle.targetX
                        duration: particle.fallDuration * 0.3
                        easing.type: Easing.InSine
                    }
                }
                
                // Opacity fade 透明度渐隐

                SequentialAnimation {
                    PauseAnimation { duration: particle.fallDuration * 0.6 }
                    NumberAnimation {
                        target: particle
                        property: "opacity"
                        from: 1
                        to: 0
                        duration: particle.fallDuration * 0.4
                        easing.type: Easing.OutQuad
                    }
                }
                
                onStopped: particle.destroy()
            }
        }
    }
}
