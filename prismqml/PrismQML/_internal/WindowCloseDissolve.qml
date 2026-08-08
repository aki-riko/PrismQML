// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import ".."
import QtQuick.Window  // Keep native Window after the library import. 库导入后保留原生 Window 名称。

// WindowCloseDissolve - Native-overlay Splash grid close effect 原生覆盖窗 Splash 网格关闭效果
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
    readonly property int _columns: Enums.windowCloseMetrics.gridColumns
    readonly property int _rows: Enums.windowCloseMetrics.gridRows
    readonly property int _cellCount: _columns * _rows
    readonly property real _maxGridDistance: (_columns + _rows - 2) / 2
    readonly property int _gridDelayRange: Enums.duration.splashExitDissolve -
                                            Enums.duration.splashGridCellFade
    readonly property var _gridBands: _buildGridBands()

    // ==================== Internal Methods 内部方法 ====================
    function _gridCellOpacity(elapsed, delay) {
        var value = Math.max(0, Math.min(1, (elapsed - delay) /
                             Enums.duration.splashGridCellFade))
        var eased = value < 0.5
            ? 4 * value * value * value
            : 1 - Math.pow(-2 * value + 2, 3) / 2
        return 1 - eased
    }

    function _buildGridBands() {
        var bands = []
        for (var index = 0; index <= Math.round(_maxGridDistance); index += 1) {
            bands.push([])
        }
        var centerColumn = (_columns - 1) / 2
        var centerRow = (_rows - 1) / 2
        for (var row = 0; row < _rows; row += 1) {
            for (var column = 0; column < _columns; column += 1) {
                var distance = Math.round(Math.abs(column - centerColumn) +
                                          Math.abs(row - centerRow))
                bands[distance].push([column, row])
            }
        }
        return bands
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
            easing.type: Easing.Linear
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

                objectName: "windowCloseGridMask"
                width: effect._columns
                height: effect._rows

                Repeater {
                    model: effect._gridBands

                    delegate: Item {
                        id: gridBand

                        required property int index
                        required property var modelData
                        readonly property int _distance: index

                        width: effect._columns
                        height: effect._rows
                        opacity: effect._gridCellOpacity(
                            effect._dissolveProgress * Enums.duration.splashExitDissolve,
                            _distance * effect._gridDelayRange / effect._maxGridDistance
                        )

                        Repeater {
                            model: gridBand.modelData

                            delegate: Rectangle {
                                required property var modelData

                                x: modelData[0]
                                y: modelData[1]
                                width: Enums.windowCloseMetrics.maskCellSize
                                height: Enums.windowCloseMetrics.maskCellSize
                                color: Enums.foregroundColor
                            }
                        }
                    }
                }
            }

            ShaderEffectSource {
                id: dissolveMaskTexture

                objectName: "windowCloseGridMaskTexture"
                anchors.fill: parent
                sourceItem: dissolveMaskContent
                hideSource: true
                live: true
                smooth: false
                textureSize: Qt.size(effect._columns, effect._rows)
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
