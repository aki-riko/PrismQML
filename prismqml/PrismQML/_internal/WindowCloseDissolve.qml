// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import QtQuick.Shapes
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
    readonly property real _rippleMaskDiameter: Math.sqrt(
        overlayClip.width * overlayClip.width + overlayClip.height * overlayClip.height
    ) + Enums.windowCloseMetrics.rippleDiameterOvershoot
    readonly property real _rippleFrontRadius: _rippleMaskDiameter *
                                                _dissolveProgress / 2
    readonly property real _ripplePeriod: _rippleMaskDiameter *
                                           Enums.windowCloseMetrics.ripplePeriodRatio *
                                           Math.sin(Math.PI * _dissolveProgress)

    // ==================== Internal Methods 内部方法 ====================
    function _rippleRadius(index) {
        var periodOffset = Math.floor(index / 2) * _ripplePeriod
        var gapOffset = index % 2 === 0 ? 0 :
                        _ripplePeriod * Enums.windowCloseMetrics.rippleGapRatio
        return Math.max(
            Enums.windowCloseMetrics.rippleDropRadius,
            _rippleFrontRadius - periodOffset - gapOffset
        )
    }

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
        frozenFrame.visible = false
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

            Item {
                id: dissolveMaskContent

                objectName: "windowCloseRippleMaskContent"
                anchors.fill: parent

                Shape {
                    id: rippleMask

                    readonly property real _radius0: effect._rippleRadius(0)
                    readonly property real _radius1: effect._rippleRadius(1)
                    readonly property real _radius2: effect._rippleRadius(2)
                    readonly property real _radius3: effect._rippleRadius(3)
                    readonly property real _radius4: effect._rippleRadius(4)
                    readonly property real _radius5: effect._rippleRadius(5)
                    readonly property real _radius6: effect._rippleRadius(6)

                    objectName: "windowCloseRippleMask"
                    anchors.fill: parent
                    preferredRendererType: Shape.CurveRenderer

                    ShapePath {
                        fillColor: Enums.foregroundColor
                        strokeColor: Enums.transparent
                        fillRule: ShapePath.OddEvenFill
                        startX: 0
                        startY: 0

                        PathLine { x: rippleMask.width; y: 0 }
                        PathLine { x: rippleMask.width; y: rippleMask.height }
                        PathLine { x: 0; y: rippleMask.height }
                        PathLine { x: 0; y: 0 }

                        PathAngleArc {
                            centerX: rippleMask.width / 2
                            centerY: rippleMask.height / 2
                            radiusX: rippleMask._radius0
                            radiusY: rippleMask._radius0
                            startAngle: 0
                            sweepAngle: Enums.windowCloseMetrics.rippleFullCircleSweep
                            moveToStart: true
                        }
                        PathAngleArc {
                            centerX: rippleMask.width / 2
                            centerY: rippleMask.height / 2
                            radiusX: rippleMask._radius1
                            radiusY: rippleMask._radius1
                            startAngle: 0
                            sweepAngle: Enums.windowCloseMetrics.rippleFullCircleSweep
                            moveToStart: true
                        }
                        PathAngleArc {
                            centerX: rippleMask.width / 2
                            centerY: rippleMask.height / 2
                            radiusX: rippleMask._radius2
                            radiusY: rippleMask._radius2
                            startAngle: 0
                            sweepAngle: Enums.windowCloseMetrics.rippleFullCircleSweep
                            moveToStart: true
                        }
                        PathAngleArc {
                            centerX: rippleMask.width / 2
                            centerY: rippleMask.height / 2
                            radiusX: rippleMask._radius3
                            radiusY: rippleMask._radius3
                            startAngle: 0
                            sweepAngle: Enums.windowCloseMetrics.rippleFullCircleSweep
                            moveToStart: true
                        }
                        PathAngleArc {
                            centerX: rippleMask.width / 2
                            centerY: rippleMask.height / 2
                            radiusX: rippleMask._radius4
                            radiusY: rippleMask._radius4
                            startAngle: 0
                            sweepAngle: Enums.windowCloseMetrics.rippleFullCircleSweep
                            moveToStart: true
                        }
                        PathAngleArc {
                            centerX: rippleMask.width / 2
                            centerY: rippleMask.height / 2
                            radiusX: rippleMask._radius5
                            radiusY: rippleMask._radius5
                            startAngle: 0
                            sweepAngle: Enums.windowCloseMetrics.rippleFullCircleSweep
                            moveToStart: true
                        }
                        PathAngleArc {
                            centerX: rippleMask.width / 2
                            centerY: rippleMask.height / 2
                            radiusX: rippleMask._radius6
                            radiusY: rippleMask._radius6
                            startAngle: 0
                            sweepAngle: Enums.windowCloseMetrics.rippleFullCircleSweep
                            moveToStart: true
                        }
                    }
                }
            }

            ShaderEffectSource {
                id: dissolveMaskTexture

                objectName: "windowCloseRippleMaskTexture"
                anchors.fill: parent
                sourceItem: dissolveMaskContent
                sourceRect: Qt.rect(0, 0, width, height)
                hideSource: true
                live: true
                smooth: true
            }

            Item {
                id: dissolveFrame

                objectName: "windowCloseDissolveFrame"
                anchors.fill: parent
                visible: effect._running
                layer.enabled: effect._running
                layer.smooth: false
                layer.effect: MultiEffect {
                    maskEnabled: true
                    maskSource: dissolveMaskTexture
                    maskThresholdMin: Enums.mask.thresholdMin
                    maskSpreadAtMin: Enums.mask.spreadFull
                }

                Image {
                    anchors.fill: parent
                    source: effect._snapshotSource
                    fillMode: Image.Stretch
                    cache: true
                    asynchronous: false
                    smooth: true
                }
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
