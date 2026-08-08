// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import QtQuick.Window  // Keep native Window after the library import. 库导入后保留原生 Window 名称。

// WindowCloseDissolve - Native-overlay ripple close effect 原生覆盖窗水滴涟漪关闭效果
Item {
    id: effect

    // ==================== Required Props 必需属性 ====================
    required property Window targetWindow
    required property Item targetItem
    required property real cornerRadius
    required property var onCaptureReady
    required property var onCloseCallback

    // ==================== Internal Props 内部属性 ====================
    property bool _running: false
    property bool _dissolving: false
    property bool _overlayFramePending: false
    property bool _usingScreenCapture: false
    property int _captureGeneration: 0
    property string _snapshotSource: ""
    property var _grabResult: null
    property real _dissolveProgress: 0

    // ==================== Internal Methods 内部方法 ====================
    function _releaseSnapshot() {
        frozenFrame.source = ""
        _snapshotSource = ""
        _grabResult = null
        _usingScreenCapture = false
    }

    function _resetVisualState() {
        _dissolveProgress = 0
        frozenFrame.visible = true
        frozenFrame.opacity = Enums.opacityLevel.visible
        frozenFrame.scale = Enums.opacityLevel.visible
    }

    function _syncOverlayGeometry() {
        var globalPosition = targetItem.mapToGlobal(0, 0)
        overlayWindow.x = Math.round(globalPosition.x)
        overlayWindow.y = Math.round(globalPosition.y)
        overlayWindow.width = Math.max(1, Math.round(targetItem.width))
        overlayWindow.height = Math.max(1, Math.round(targetItem.height))
    }

    function _setSnapshotSource(source, grabResult, screenCapture) {
        if (!_running || !source) return
        _grabResult = grabResult
        _usingScreenCapture = screenCapture
        _snapshotSource = source
        frozenFrame.source = source
        Qt.callLater(_showOverlayWhenReady)
    }

    function _showOverlayWhenReady() {
        if (!_running || !_snapshotSource || frozenFrame.status !== Image.Ready) return
        _overlayFramePending = true
        overlayWindow.visible = true
        overlayWindow.requestUpdate()
    }

    function _captureWithItem(generation) {
        _usingScreenCapture = false
        var accepted = targetItem.grabToImage(function(result) {
            if (!effect._running || generation !== effect._captureGeneration) return
            effect._setSnapshotSource(result.url, result, false)
        })
        if (!accepted) _startFallbackClose("item grab request rejected")
    }

    function _captureSnapshot(generation) {
        if (!_running || generation !== _captureGeneration) return
        _syncOverlayGeometry()
        if (typeof AcrylicHelper !== "undefined" && AcrylicHelper &&
                typeof AcrylicHelper.grabWindowFrame === "function") {
            var source = AcrylicHelper.grabWindowFrame(
                targetWindow,
                Math.round(targetItem.x),
                Math.round(targetItem.y),
                Math.round(targetItem.width),
                Math.round(targetItem.height)
            )
            if (source) {
                _setSnapshotSource(source, null, true)
                return
            }
        }
        _captureWithItem(generation)
    }

    function _beginDissolve() {
        if (!_running || !_overlayFramePending) return
        _overlayFramePending = false
        targetWindow.opacity = Enums.opacityLevel.invisible
        onCaptureReady()
        _dissolving = true
        frozenFrame.opacity = Enums.opacityLevel.invisible
        closeAnimation.start()
    }

    function _startFallbackClose(reason) {
        if (!_running) return
        console.error("WindowCloseDissolve: " + reason)
        overlayWindow.visible = false
        _overlayFramePending = false
        _dissolving = false
        fallbackCloseAnimation.start()
    }

    function _completeClose() {
        _running = false
        _dissolving = false
        _overlayFramePending = false
        overlayWindow.visible = false
        _releaseSnapshot()
        onCloseCallback()
    }

    function start() {
        stop()
        _running = true
        _captureGeneration += 1
        targetWindow.opacity = Enums.opacityLevel.visible
        _resetVisualState()
        var generation = _captureGeneration
        Qt.callLater(function() { effect._captureSnapshot(generation) })
    }

    function stop() {
        _captureGeneration += 1
        closeAnimation.stop()
        fallbackCloseAnimation.stop()
        _running = false
        _dissolving = false
        _overlayFramePending = false
        overlayWindow.visible = false
        _resetVisualState()
        _releaseSnapshot()
        if (targetWindow) targetWindow.opacity = Enums.opacityLevel.visible
    }

    objectName: "windowCloseDissolve"
    anchors.fill: parent
    visible: false

    // ==================== Content 内容 ====================
    SequentialAnimation {
        id: closeAnimation

        NumberAnimation {
            target: effect
            property: "_dissolveProgress"
            to: Enums.opacityLevel.visible
            duration: Enums.duration.splashExitDissolve
            easing.type: Easing.OutQuad
        }
        ScriptAction { script: effect._completeClose() }
    }

    SequentialAnimation {
        id: fallbackCloseAnimation

        NumberAnimation {
            target: effect.targetWindow
            property: "opacity"
            to: Enums.opacityLevel.invisible
            duration: Enums.duration.splashExitDissolve
            easing.type: Easing.InCubic
        }
        ScriptAction { script: effect._completeClose() }
    }

    Window {
        id: overlayWindow

        objectName: "windowCloseOverlayWindow"
        visible: false
        opacity: Enums.opacityLevel.visible
        color: Enums.transparent
        flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoFluentShadowWindowHint
        transientParent: null

        onFrameSwapped: effect._beginDissolve()

        Rectangle {
            id: overlayClip

            anchors.fill: parent
            color: Enums.transparent
            radius: effect.cornerRadius
            clip: true

            ShaderEffect {
                id: rippleFrame

                property variant source: frozenFrame
                property real progress: effect._dissolveProgress
                property real aspectRatio: width / Math.max(height, 1)
                property real tailLength: Enums.windowCloseMetrics.rippleTailLength
                property real waveFrequency: Enums.windowCloseMetrics.rippleWaveFrequency
                property real waveDispersion: Enums.windowCloseMetrics.rippleWaveDispersion
                property real waveDamping: Enums.windowCloseMetrics.rippleWaveDamping
                property real waveAmplitude: Enums.windowCloseMetrics.rippleWaveAmplitude
                property real highlightStrength: Enums.windowCloseMetrics.rippleHighlightStrength
                property real frontSoftness: Enums.windowCloseMetrics.rippleFrontSoftness
                property real frontRefractionWidth: Enums.windowCloseMetrics.rippleFrontRefractionWidth
                property real crestSharpness: Enums.windowCloseMetrics.rippleCrestSharpness
                property real rippleOpacity: Enums.windowCloseMetrics.rippleOpacity
                property real finishFadeStart: Enums.windowCloseMetrics.rippleFinishFadeStart

                objectName: "windowCloseRippleFrame"
                anchors.fill: parent
                visible: effect._dissolving
                blending: true
                fragmentShader: Qt.resolvedUrl("../shaders/window_close_ripple.frag.qsb")
            }

            Image {
                id: frozenFrame

                objectName: "windowCloseFrozenFrame"
                anchors.fill: parent
                z: Enums.zIndex.controls
                source: ""
                fillMode: Image.Stretch
                cache: true
                asynchronous: false
                smooth: true
                transformOrigin: Item.Center
                onStatusChanged: {
                    if (!effect._running) return
                    if (status === Image.Ready) {
                        effect._showOverlayWhenReady()
                    } else if (status === Image.Error) {
                        if (effect._usingScreenCapture) {
                            effect._captureWithItem(effect._captureGeneration)
                        } else {
                            effect._startFallbackClose("snapshot image load failed")
                        }
                    }
                }
            }
        }
    }
}
