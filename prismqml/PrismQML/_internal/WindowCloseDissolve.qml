// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
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
    readonly property int _columns: Enums.splashScreenMetrics.exitGridColumns
    readonly property int _rows: Enums.splashScreenMetrics.exitGridRows
    readonly property int _cellCount: _columns * _rows

    // ==================== Internal Methods 内部方法 ====================
    function _gridCellOpacity(elapsed, delay) {
        var value = Math.max(0, Math.min(1, (elapsed - delay) /
                             Enums.duration.splashGridCellFade))
        var eased = value < 0.5
            ? 4 * value * value * value
            : 1 - Math.pow(-2 * value + 2, 3) / 2
        return 1 - eased
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

            Repeater {
                id: dissolveGrid

                model: effect._cellCount

                delegate: Item {
                    id: gridCell

                    readonly property int _column: index % effect._columns
                    readonly property int _row: Math.floor(index / effect._columns)
                    readonly property real _centerColumn: (effect._columns - 1) / 2
                    readonly property real _centerRow: (effect._rows - 1) / 2
                    readonly property int _delay: Math.round((
                        Math.abs(gridCell._column - gridCell._centerColumn) +
                        Math.abs(gridCell._row - gridCell._centerRow)
                    ) * Enums.duration.splashGridDelayStep)

                    objectName: "windowCloseGridCell_" + index
                    x: gridCell._column * overlayClip.width / effect._columns
                    y: gridCell._row * overlayClip.height / effect._rows
                    width: overlayClip.width / effect._columns +
                           Enums.splashScreenMetrics.exitGridOverlap
                    height: overlayClip.height / effect._rows +
                            Enums.splashScreenMetrics.exitGridOverlap
                    clip: true
                    opacity: effect._gridCellOpacity(
                        effect._dissolveProgress * Enums.duration.splashExitDissolve,
                        gridCell._delay
                    )
                    visible: effect._dissolving

                    Image {
                        x: -gridCell.x
                        y: -gridCell.y
                        width: overlayClip.width
                        height: overlayClip.height
                        source: effect._snapshotSource
                        fillMode: Image.Stretch
                        cache: true
                        asynchronous: false
                        smooth: true
                    }
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
