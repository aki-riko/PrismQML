// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../.."
import "_internal" as Internal
import QtQuick  // Keep native types unprefixed after library import 库导入后保留原生类型无前缀

// QMLPage - Loading page with a single-aperture transition 单层光圈过渡加载页
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string text: { Translator._v; return Translator.tr("loading") }  // Loading message 加载提示
    property bool running: visible                  // Run animation while loading 加载时运行动画
    property color backgroundColor: Enums.backgroundColor  // Page background 页面背景
    property color transitionBackgroundColor: backgroundColor  // Aperture surface 光圈过渡表面
    property color color: _transitionOpaque
        ? _transitionSurfaceColor : backgroundColor
    property real transitionBackgroundOpacity:
        Enums.lazyLoadingTransitionMetrics.surfaceOpacity
    property real circleMinimumRadius: progressRing.width / 2

    // ==================== Readonly State 只读状态 ====================
    readonly property bool entering: _entering       // Covering the old page 正在覆盖旧页
    readonly property bool finishing: _finishing     // Revealing the target page 正在揭示目标页
    readonly property color _transitionSurfaceColor: Qt.rgba(
        transitionBackgroundColor.r,
        transitionBackgroundColor.g,
        transitionBackgroundColor.b,
        transitionBackgroundColor.a
            * Math.max(Enums.opacityLevel.invisible,
                       Math.min(Enums.opacityLevel.visible, transitionBackgroundOpacity))
    )

    // ==================== Internal Props 内部属性 ====================
    property bool _entering: false
    property bool _finishing: false
    property bool _finishRequested: false
    property bool _transitionOpaque: false
    property int _transitionPhase: 0

    // ==================== Signals 信号 ====================
    signal entered()   // Emitted after the aperture covers the old page 光圈覆盖旧页后触发
    signal finished()  // Emitted after the page is removed 页面移除后触发

    // ==================== Public Methods 公开方法 ====================
    function start() {
        circleTransition.stop()
        control._entering = true
        control._finishing = false
        control._finishRequested = false
        control._transitionOpaque = true
        control._transitionPhase = 1
        control.visible = true
        contentColumn.opacity = Enums.opacityLevel.visible
        contentColumn.scale = Enums.opacityLevel.visible
        circleTransition.start(false)
    }

    function finish() {
        if (control._finishing || !control.visible) return
        control._finishing = true
        if (control._entering) {
            control._finishRequested = true
            return
        }
        control._beginTargetReveal()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _beginTargetReveal() {
        control._transitionPhase = 2
        control._transitionOpaque = true
        circleTransition.start(true)
    }

    function _completeCover() {
        control._transitionPhase = 0
        control._entering = false
        control.entered()
        if (!control._finishRequested) return
        control._finishRequested = false
        control._beginTargetReveal()
    }

    function _completeTargetReveal() {
        control.visible = false
        control.finished()
        control._entering = false
        control._finishing = false
        control._finishRequested = false
        control._transitionOpaque = false
        control._transitionPhase = 0
    }

    clip: true

    onVisibleChanged: {
        if (visible || control._finishing) return
        circleTransition.stop()
        control._entering = false
        control._finishRequested = false
        control._transitionOpaque = false
        control._transitionPhase = 0
    }

    Internal.QMLPageCircleTransition {
        id: circleTransition

        objectName: "qmlPageCircleTransition"
        onFinished: {
            if (control._transitionPhase === 1) {
                control._completeCover()
            } else if (control._transitionPhase === 2) {
                control._completeTargetReveal()
            }
        }
    }

    // ==================== Content 内容 ====================
    Rectangle {
        id: transitionSurface

        anchors.fill: parent
        color: control.color

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

    ShaderEffectSource {
        id: transitionSurfaceTexture

        anchors.fill: parent
        sourceItem: transitionSurface
        hideSource: circleTransition.running
        live: true
        recursive: true
        visible: false
    }

    Internal.QMLPageCircleFrame {
        objectName: "qmlPageCircleFrame"
        anchors.fill: parent
        source: transitionSurfaceTexture
        progress: circleTransition.progress
        minimumRadiusPixels: control.circleMinimumRadius
        revealTarget: circleTransition.revealTarget
        visible: circleTransition.running
    }

    SequentialAnimation {
        id: ringBreatheAnimation

        running: control.visible && !control.entering
            && !control.finishing && control.running
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
}
