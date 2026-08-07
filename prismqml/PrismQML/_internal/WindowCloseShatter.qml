// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import QtQuick.Window  // Keep native Window after the library import. 库导入后保留原生 Window 名称。

// WindowCloseShatter - Frozen-frame shatter close effect 冻结画面粉碎关闭效果
Item {
    id: effect

    // ==================== Required Props 必需属性 ====================
    required property Window targetWindow
    required property Item targetItem
    required property var onCaptureReady
    required property var onCloseCallback

    // ==================== Internal Props 内部属性 ====================
    property real progress: Enums.opacityLevel.invisible
    property bool _running: false
    readonly property int _columns: Enums.window.closeShatterColumns
    readonly property int _rows: Enums.window.closeShatterRows
    readonly property int _shardCount: _columns * _rows
    readonly property int _noiseMultiplier: 37
    readonly property int _noiseOffset: 17
    readonly property int _noiseModulus: 101
    readonly property int _noiseMaximum: _noiseModulus - 1

    // ==================== Internal Methods 内部方法 ====================
    function _clamp(value) {
        return Math.max(Enums.opacityLevel.invisible,
                        Math.min(Enums.opacityLevel.visible, value))
    }

    function _noise(indexValue, salt) {
        var mixed = (indexValue + 1) * (salt * _noiseMultiplier + _noiseOffset)
        return (mixed % _noiseModulus) / _noiseMaximum
    }

    function _scheduleShardUpdates() {
        for (var index = 0; index < shards.count; index++) {
            var shard = shards.itemAt(index)
            if (shard) shard.scheduleUpdate()
        }
    }

    function start() {
        stop()
        progress = Enums.opacityLevel.invisible
        visible = true
        _running = true
        targetWindow.opacity = Enums.opacityLevel.visible
        frozenFrame.scheduleUpdate()
        closeAnimation.start()
    }

    function stop() {
        closeAnimation.stop()
        _running = false
        progress = Enums.opacityLevel.invisible
        visible = false
        if (targetWindow) targetWindow.opacity = Enums.opacityLevel.visible
    }

    objectName: "windowCloseShatter"
    anchors.fill: parent
    z: Enums.zIndex.overlay
    visible: false

    onProgressChanged: {
        if (!_running || !targetWindow) return
        var fadeStart = Enums.window.closeShatterWindowFadeStart
        var fadeProgress = _clamp((progress - fadeStart) /
                                  (Enums.opacityLevel.visible - fadeStart))
        targetWindow.opacity = Enums.opacityLevel.visible - fadeProgress
    }

    // ==================== Content 内容 ====================
    SequentialAnimation {
        id: closeAnimation

        PauseAnimation { duration: Enums.window.closeShatterCaptureDelayMs }
        ScriptAction { script: effect._scheduleShardUpdates() }
        PauseAnimation { duration: Enums.window.closeShatterCaptureDelayMs }
        ScriptAction { script: effect.onCaptureReady() }
        NumberAnimation {
            target: effect
            property: "progress"
            from: Enums.opacityLevel.invisible
            to: Enums.opacityLevel.visible
            duration: Enums.duration.verySlow
            easing.type: Easing.Linear
        }
        ScriptAction {
            script: {
                effect._running = false
                effect.onCloseCallback()
            }
        }
    }

    ShaderEffectSource {
        id: frozenFrame

        objectName: "windowCloseFrozenFrame"
        x: effect.targetItem.x
        y: effect.targetItem.y
        width: effect.targetItem.width
        height: effect.targetItem.height
        visible: false
        sourceItem: effect.targetItem
        hideSource: false
        live: false
        recursive: false
        smooth: true
    }

    Repeater {
        id: shards

        model: effect._shardCount

        delegate: ShaderEffectSource {
            id: shard

            readonly property int _column: index % effect._columns
            readonly property int _row: Math.floor(index / effect._columns)
            readonly property real _cellWidth: effect.targetItem.width / effect._columns
            readonly property real _cellHeight: effect.targetItem.height / effect._rows
            readonly property real _randomX: effect._noise(index, _row + 1)
            readonly property real _randomY: effect._noise(index, _column + 1)
            readonly property real _randomRotation: effect._noise(index, _row + _column + 1)
            readonly property real _waveDistance:
                (effect._columns - 1 - _column) +
                _row * Enums.window.closeShatterRowWeight +
                _randomRotation * Enums.window.closeShatterRandomWaveWeight
            readonly property real _maxWaveDistance:
                (effect._columns - 1) +
                (effect._rows - 1) * Enums.window.closeShatterRowWeight +
                Enums.window.closeShatterRandomWaveWeight
            readonly property real _startProgress:
                _waveDistance / _maxWaveDistance * Enums.window.closeShatterWaveSpread
            readonly property real _localProgress: effect._clamp(
                (effect.progress - _startProgress) /
                (Enums.opacityLevel.visible - _startProgress)
            )
            readonly property real _baseX: effect.targetItem.x + _column * _cellWidth
            readonly property real _baseY: effect.targetItem.y + _row * _cellHeight
            readonly property real _outwardDirection:
                2 * _column / (effect._columns - 1) - 1
            readonly property real _horizontalTravel:
                effect.targetItem.width * (
                    Enums.window.closeShatterHorizontalTravelRatio * (2 * _randomX - 1) +
                    Enums.window.closeShatterOutwardTravelRatio * _outwardDirection
                )
            readonly property real _fallFactor:
                Enums.window.closeShatterMinFallFactor +
                (Enums.opacityLevel.visible - Enums.window.closeShatterMinFallFactor) *
                _randomY
            readonly property real _fadeProgress: effect._clamp(
                (_localProgress - Enums.window.closeShatterFadeStart) /
                (Enums.opacityLevel.visible - Enums.window.closeShatterFadeStart)
            )

            objectName: "windowCloseShard_" + index
            x: _baseX + _horizontalTravel * _localProgress
            y: _baseY + effect.targetItem.height * Enums.window.closeShatterFallRatio *
               _fallFactor * _localProgress * _localProgress
            width: _cellWidth + (_column < effect._columns - 1
                                 ? Enums.window.closeShatterCellOverlap : 0)
            height: _cellHeight + (_row < effect._rows - 1
                                   ? Enums.window.closeShatterCellOverlap : 0)
            opacity: Enums.opacityLevel.visible - _fadeProgress
            scale: Enums.opacityLevel.visible -
                   Enums.window.closeShatterScaleLoss * _localProgress
            rotation: (2 * _randomRotation - 1) *
                      Enums.window.closeShatterRotationDegrees * _localProgress
            transformOrigin: Item.Center
            sourceItem: frozenFrame
            sourceRect: Qt.rect(_column * _cellWidth, _row * _cellHeight, width, height)
            hideSource: false
            live: false
            recursive: false
            smooth: true
            antialiasing: true
        }
    }
}
