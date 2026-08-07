// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import QtQuick.Window  // Keep native Window after the library import. 库导入后保留原生 Window 名称。

// WindowCloseFold - Accordion fold-to-close-button effect 手风琴式折向关闭按钮效果
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
    readonly property int _columns: Enums.window.closeFoldColumns

    // ==================== Internal Methods 内部方法 ====================
    function _clamp(value) {
        return Math.max(Enums.opacityLevel.invisible,
                        Math.min(Enums.opacityLevel.visible, value))
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

    objectName: "windowCloseFold"
    anchors.fill: parent
    z: Enums.zIndex.overlay
    visible: false

    onProgressChanged: {
        if (!_running || !targetWindow) return
        var fadeStart = Enums.window.closeFoldWindowFadeStart
        var fadeProgress = _clamp((progress - fadeStart) /
                                  (Enums.opacityLevel.visible - fadeStart))
        targetWindow.opacity = Enums.opacityLevel.visible - fadeProgress
    }

    // ==================== Content 内容 ====================
    SequentialAnimation {
        id: closeAnimation

        PauseAnimation { duration: Enums.window.closeFoldCaptureDelayMs }
        PauseAnimation { duration: Enums.window.closeFoldCaptureDelayMs }
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
        id: foldPanels

        model: effect._columns

        delegate: ShaderEffectSource {
            id: panel

            readonly property int _column: index
            readonly property real _cellWidth: effect.targetItem.width / effect._columns
            readonly property real _panelWidth: _cellWidth +
                (_column < effect._columns - 1 ? Enums.window.closeFoldCellOverlap : 0)
            readonly property real _startProgress:
                (effect._columns - 1 - _column) /
                (effect._columns - 1) * Enums.window.closeFoldWaveSpread
            readonly property real _localProgress: effect._clamp(
                (effect.progress - _startProgress) /
                (Enums.opacityLevel.visible - _startProgress)
            )
            readonly property real _motionProgress: Enums.opacityLevel.visible - Math.pow(
                Enums.opacityLevel.visible - _localProgress,
                Enums.window.closeFoldMotionEasePower
            )
            readonly property real _collapseProgress: effect._clamp(
                (_localProgress - Enums.window.closeFoldCollapseStart) /
                (Enums.opacityLevel.visible - Enums.window.closeFoldCollapseStart)
            )
            readonly property real _baseX: effect.targetItem.x + _column * _cellWidth
            readonly property real _targetX:
                effect.targetItem.x + effect.targetItem.width - _panelWidth
            readonly property real _fadeProgress: effect._clamp(
                (_localProgress - Enums.window.closeFoldFadeStart) /
                (Enums.opacityLevel.visible - Enums.window.closeFoldFadeStart)
            )
            readonly property real _foldDirection: _column % 2 === 0 ? 1 : -1
            readonly property real _foldAngle:
                _foldDirection * Enums.window.closeFoldAngleDegrees * _motionProgress

            objectName: "windowCloseFoldPanel_" + index
            x: _baseX + (_targetX - _baseX) * _motionProgress
            y: effect.targetItem.y
            width: _panelWidth
            height: effect.targetItem.height
            z: effect._columns - _column
            opacity: Enums.opacityLevel.visible - _fadeProgress
            scale: Enums.opacityLevel.visible -
                   (Enums.opacityLevel.visible - Enums.window.closeFoldFinalScale) *
                   _collapseProgress
            transformOrigin: Item.TopRight
            sourceItem: frozenFrame
            sourceRect: Qt.rect(_column * _cellWidth, 0, _panelWidth,
                                effect.targetItem.height)
            hideSource: false
            live: true
            recursive: false
            smooth: true
            antialiasing: true

            transform: Rotation {
                origin.x: panel._foldDirection > 0 ? 0 : panel.width
                origin.y: panel.height / 2
                axis.x: 0
                axis.y: 1
                axis.z: 0
                angle: panel._foldAngle
            }
        }
    }
}
