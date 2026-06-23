// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import ".."

// ToggleAnimation - Reusable toggle animation effect 可复用的切换动画效果
// Usage 使用方式:
//   ToggleAnimation {
//       target: myButton
//       running: checked  // Bind to checked state 绑定到checked状态
//   }
Item {
    id: root
    
    // ==================== Public Props 公开属性 ====================
    property Item target: parent           // Target item to animate 动画目标
    property bool running: false           // Trigger animation 触发动画
    property int duration: Enums.duration.medium  // Animation duration 动画时长
    
    // ==================== Internal 内部 ====================
    property bool _lastState: false
    
    onRunningChanged: {
        if (running !== _lastState) {
            _lastState = running
            bounceAnim.restart()
        }
    }
    
    // Bounce animation sequence 弹跳动画序列
    SequentialAnimation {
        id: bounceAnim
        
        // Quick press down 快速按下
        ParallelAnimation {
            NumberAnimation {
                target: root.target
                property: "scale"
                to: 0.85
                duration: root.duration * 0.25
                easing.type: Easing.OutQuad
            }
        }
        
        // Bounce up with overshoot 带过冲的弹起
        NumberAnimation {
            target: root.target
            property: "scale"
            to: 1.05
            duration: root.duration * 0.35
            easing.type: Easing.OutQuad
        }
        
        // Settle back 回弹稳定
        NumberAnimation {
            target: root.target
            property: "scale"
            to: 1.0
            duration: root.duration * 0.4
            easing.type: Easing.OutElastic
            easing.amplitude: 1.2
            easing.period: 0.4
        }
    }
}
