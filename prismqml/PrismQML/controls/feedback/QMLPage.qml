// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../.."
import QtQuick  // Keep native types unprefixed after library import 库导入后保留原生类型无前缀

// QMLPage - Transparent lazy-loading wait indicator 透明懒加载等待指示页
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string text: { Translator._v; return Translator.tr("loading") }  // Loading message 加载提示
    property bool running: visible && !finishing    // Run animation while waiting 等待时运行动画
    property color backgroundColor: Enums.backgroundColor  // Page background 页面背景

    // ==================== Readonly State 只读状态 ====================
    readonly property bool finishing: _finishing     // Hiding the wait indicator 正在隐藏等待指示

    // ==================== Internal Props 内部属性 ====================
    property bool _finishing: false

    // ==================== Signals 信号 ====================
    signal finished()  // Emitted after the page is removed 页面移除后触发

    // ==================== Public Methods 公开方法 ====================
    function start() {
        finishAnimation.stop()
        finishGuard.stop()
        control._finishing = false
        control.visible = true
        contentColumn.opacity = Enums.opacityLevel.visible
        contentColumn.scale = Enums.opacityLevel.visible
    }

    function finish() {
        if (control._finishing || !control.visible) return
        control._finishing = true
        finishAnimation.restart()
        // An exit without an owner must still end. When the animation callback
        // never lands (window hidden during startup, scene graph torn down,
        // competing animation) the wait indicator would otherwise stay parked
        // on screen; the guard finishes the same exit shortly after its
        // duration. A normal exit lands first, so visible behaviour is
        // unchanged. / 退场必须有终点。动画回调未落地时(启动期窗口隐藏、场景图
        // 被拆、竞争动画)等待指示会永久停在屏幕上; 看门狗在退场时长稍后完成同一次
        // 退场。正常退场先落地, 因此可见行为不变。
        finishGuard.restart()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _completeFinish() {
        finishAnimation.stop()
        finishGuard.stop()
        control.visible = false
        control.finished()
        control._finishing = false
        contentColumn.opacity = Enums.opacityLevel.visible
        contentColumn.scale = Enums.opacityLevel.visible
    }

    clip: true

    onVisibleChanged: {
        if (visible || control._finishing) return
        finishAnimation.stop()
        control._finishing = false
        contentColumn.opacity = Enums.opacityLevel.visible
        contentColumn.scale = Enums.opacityLevel.visible
    }

    // ==================== Content 内容 ====================
    Rectangle {
        id: transitionSurface

        anchors.fill: parent
        color: control.backgroundColor

        Column {
            id: contentColumn

            objectName: "qmlPageContent"
            anchors.centerIn: parent
            opacity: Enums.opacityLevel.visible
            scale: Enums.opacityLevel.visible
            transformOrigin: Item.Center
            spacing: Enums.spacing.xl

            ProgressRing {
                id: progressRing

                objectName: "qmlPageProgressRing"
                anchors.horizontalCenter: parent.horizontalCenter
                width: Enums.controlSize.navBarHeight
                height: Enums.controlSize.navBarHeight
                indeterminate: control.running
                indeterminateStyle: Enums.progress.indeterminate_style_fixed_arc
                paused: !control.running
                strokeWidth: Enums.controlSize.progressStrokeWidth
                spinDuration: Enums.duration.scroll
                trackColorLight: Enums.transparent
                trackColorDark: Enums.transparent
            }

            Label {
                objectName: "qmlPageLabel"
                anchors.horizontalCenter: parent.horizontalCenter
                text: control.text
                type: Enums.label.type_body
                visible: control.text !== ""
            }
        }
    }

    SequentialAnimation {
        id: ringBreatheAnimation

        running: control.visible && !control.finishing && control.running
        loops: Animation.Infinite
        onRunningChanged: {
            if (!running) progressRing.scale = Enums.opacityLevel.visible
        }

        NumberAnimation {
            target: progressRing
            property: "scale"
            from: Enums.lazyLoadingTransitionMetrics.breatheMinScale
            to: Enums.lazyLoadingTransitionMetrics.breatheMaxScale
            duration: Enums.lazyLoadingTransitionMetrics.breatheHalfDuration
            easing.type: Easing.InOutSine
        }

        NumberAnimation {
            target: progressRing
            property: "scale"
            from: Enums.lazyLoadingTransitionMetrics.breatheMaxScale
            to: Enums.lazyLoadingTransitionMetrics.breatheMinScale
            duration: Enums.lazyLoadingTransitionMetrics.breatheHalfDuration
            easing.type: Easing.InOutSine
        }
    }

    ParallelAnimation {
        id: finishAnimation

        onFinished: control._completeFinish()

        NumberAnimation {
            target: contentColumn
            property: "opacity"
            from: Enums.opacityLevel.visible
            to: Enums.opacityLevel.invisible
            duration: Enums.duration.fast
            easing.type: Easing.InCubic
        }

        NumberAnimation {
            target: contentColumn
            property: "scale"
            from: Enums.opacityLevel.visible
            to: Enums.lazyLoadingTransitionMetrics.breatheMinScale
            duration: Enums.duration.fast
            easing.type: Easing.InCubic
        }
    }

    // Exit watchdog. Duration is the exit animation plus a safety margin, so a
    // normal exit always finishes first and only a dropped callback reaches it.
    // 退场看门狗。时长取退场动画加安全余量, 正常退场总是先完成, 只有回调丢失时
    // 才会触发。
    Timer {
        id: finishGuard

        objectName: "qmlPageFinishGuard"
        interval: Enums.duration.fast + Enums.duration.normal
        repeat: false
        onTriggered: control._completeFinish()
    }
}
