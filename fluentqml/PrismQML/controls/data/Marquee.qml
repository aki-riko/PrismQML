// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../data"

// Marquee - Scrolling text component 滚动文字组件
Item {
    id: control
    
    property string text: ""
    property int speed: 50  // Pixels per second 像素/秒
    property bool running: true
    property bool forceScroll: false  // Force scroll even if text fits 强制滚动即使文字不超出
    property int pauseDuration: Enums.duration.marquee
    
    implicitWidth: 200
    implicitHeight: Enums.controlSize.statusBarHeight
    clip: true
    
    // Internal: track if text needs scrolling 内部：跟踪文本是否需要滚动
    readonly property bool _needsScroll: forceScroll || marqueeText.implicitWidth > control.width

    // ==================== Public Methods 公共方法 ====================
    // Internal function to check and start animation 内部函数检查并启动动画
    function _tryStartAnimation() {
        if (running && _needsScroll && width > 0 && !scrollAnim.running) {
            marqueeText.x = 0
            scrollAnim.restart()
        } else if (!running || !_needsScroll) {
            scrollAnim.stop()
            marqueeText.x = 0
        }
    }

    function getText() { return text }

    // Start 开始滚动
    function start() { running = true }

    // Stop 停止滚动
    function stop() { running = false }

    Label {
        id: marqueeText
        type: Enums.label.type_body
        text: control.text
        y: (parent.height - height) / 2
        x: 0
    }
    
    // Scroll animation 滚动动画
    SequentialAnimation {
        id: scrollAnim
        loops: Animation.Infinite
        
        PauseAnimation { duration: control.pauseDuration }
        
        NumberAnimation {
            target: marqueeText
            property: "x"
            from: 0
            to: -marqueeText.implicitWidth - 20
            duration: Math.max(100, (marqueeText.implicitWidth + 20) * 1000 / control.speed)
        }
        
        ScriptAction { script: marqueeText.x = control.width }
        
        NumberAnimation {
            target: marqueeText
            property: "x"
            from: control.width
            to: 0
            duration: Math.max(100, control.width * 1000 / control.speed)
        }
    }
    
    // Use Timer to ensure layout is complete 使用Timer确保布局完成
    Timer {
        id: startTimer
        interval: 100
        repeat: false
        onTriggered: control._tryStartAnimation()
    }
    
    onWidthChanged: startTimer.restart()
    on_NeedsScrollChanged: startTimer.restart()
    onRunningChanged: _tryStartAnimation()
    onForceScrollChanged: startTimer.restart()
    
    Component.onCompleted: startTimer.start()
}
