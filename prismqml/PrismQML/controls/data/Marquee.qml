// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../data"

// Marquee - Scrolling text component 滚动文字组件
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string text: ""
    property int speed: 50  // Pixels per second 像素/秒
    property bool running: true
    property bool forceScroll: false  // Force scroll even if text fits 强制滚动即使文字不超出
    property int pauseDuration: Enums.duration.marquee
    property int labelType: Enums.label.type_body
    property int fontPixelSize: Enums.typography.body
    property color customTextColor: Enums.transparent
    property int scrollGap: Enums.spacing.l

    // ==================== Readonly State 只读状态 ====================
    // Internal: track if text needs scrolling 内部：跟踪文本是否需要滚动
    readonly property bool _needsScroll: forceScroll || marqueeText.implicitWidth > control.width
    readonly property int _safeSpeed: Math.max(1, speed)
    readonly property int _safeScrollGap: Math.max(0, scrollGap)
    readonly property real _scrollDistance: Math.max(0, marqueeText.implicitWidth + _safeScrollGap)
    readonly property int _scrollDuration: Math.max(Enums.duration.fast, _scrollDistance * 1000 / _safeSpeed)

    // ==================== Public Methods 公开方法 ====================
    function getText() { return text }

    // Start 开始滚动
    function start() { running = true }

    // Stop 停止滚动
    function stop() { running = false }

    // ==================== Internal Methods 内部方法 ====================
    // Internal function to check and start animation 内部函数检查并启动动画
    function _tryStartAnimation() {
        if (running && _needsScroll && width > 0 && !scrollAnim.running) {
            marqueeContent.x = 0
            scrollAnim.restart()
        } else if (!running || !_needsScroll) {
            scrollAnim.stop()
            marqueeContent.x = 0
        }
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: 200
    implicitHeight: Enums.controlSize.statusBarHeight
    clip: true
    onWidthChanged: startTimer.restart()
    on_NeedsScrollChanged: startTimer.restart()
    on_ScrollDistanceChanged: startTimer.restart()
    onRunningChanged: _tryStartAnimation()
    onForceScrollChanged: startTimer.restart()
    onScrollGapChanged: startTimer.restart()
    onSpeedChanged: startTimer.restart()
    onPauseDurationChanged: startTimer.restart()
    Component.onCompleted: startTimer.start()

    // ==================== Content 内容 ====================
    Item {
        id: marqueeContent
        objectName: "marqueeContent"

        x: 0
        width: control._scrollDistance + marqueeTextCopy.implicitWidth
        height: parent.height

        Label {
            id: marqueeText
            objectName: "marqueeText"

            type: control.labelType
            text: control.text
            y: (parent.height - height) / 2
            x: 0
            font.pixelSize: control.fontPixelSize
            customTextColor: control.customTextColor
        }

        Label {
            id: marqueeTextCopy
            objectName: "marqueeTextCopy"

            type: control.labelType
            text: control.text
            y: marqueeText.y
            x: control._scrollDistance
            font.pixelSize: control.fontPixelSize
            customTextColor: control.customTextColor
            visible: control._needsScroll
        }
    }
    
    // Scroll animation 滚动动画
    SequentialAnimation {
        id: scrollAnim
        loops: Animation.Infinite
        
        PauseAnimation { duration: Math.max(0, control.pauseDuration) }
        
        NumberAnimation {
            target: marqueeContent
            property: "x"
            from: 0
            to: -control._scrollDistance
            duration: control._scrollDuration
        }
    }
    
    // Use Timer to ensure layout is complete 使用Timer确保布局完成
    Timer {
        id: startTimer
        interval: 100
        repeat: false
        onTriggered: control._tryStartAnimation()
    }
}
