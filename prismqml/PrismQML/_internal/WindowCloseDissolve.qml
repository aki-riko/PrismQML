// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import QtQuick.Window  // Keep native Window after the library import. 库导入后保留原生 Window 名称。

// WindowCloseDissolve - Splash-style grid dissolve close effect Splash 风格网格溶解关闭效果
Item {
    id: effect

    // ==================== Required Props 必需属性 ====================
    required property Window targetWindow
    required property Item targetItem
    required property color backgroundColor
    required property var onCaptureReady
    required property var onCloseCallback

    // ==================== Internal Props 内部属性 ====================
    property bool _running: false
    property bool _dissolving: false
    readonly property int _columns: Enums.splashScreenMetrics.exitGridColumns
    readonly property int _rows: Enums.splashScreenMetrics.exitGridRows
    readonly property int _cellCount: _columns * _rows

    // ==================== Internal Methods 内部方法 ====================
    function _resetCells() {
        for (var index = 0; index < dissolveGrid.count; index++) {
            var cell = dissolveGrid.itemAt(index)
            if (cell) cell.opacity = Enums.opacityLevel.visible
        }
    }

    function start() {
        stop()
        _resetCells()
        frozenFrame.opacity = Enums.opacityLevel.visible
        frozenFrame.scale = Enums.opacityLevel.visible
        visible = true
        _running = true
        targetWindow.opacity = Enums.opacityLevel.visible
        frozenFrame.scheduleUpdate()
        closeAnimation.start()
    }

    function stop() {
        closeAnimation.stop()
        _running = false
        _dissolving = false
        frozenFrame.opacity = Enums.opacityLevel.visible
        frozenFrame.scale = Enums.opacityLevel.visible
        _resetCells()
        visible = false
        if (targetWindow) targetWindow.opacity = Enums.opacityLevel.visible
    }

    objectName: "windowCloseDissolve"
    anchors.fill: parent
    z: Enums.zIndex.overlay
    visible: false

    // ==================== Content 内容 ====================
    SequentialAnimation {
        id: closeAnimation

        PauseAnimation { duration: Enums.window.closeAnimationCaptureDelayMs }
        PauseAnimation { duration: Enums.window.closeAnimationCaptureDelayMs }
        ScriptAction {
            script: {
                effect._dissolving = true
                effect.onCaptureReady()
            }
        }
        ParallelAnimation {
            NumberAnimation {
                target: frozenFrame
                property: "opacity"
                to: Enums.opacityLevel.invisible
                duration: Enums.duration.splashGridContentFade
                easing.type: Easing.InCubic
            }
            NumberAnimation {
                target: frozenFrame
                property: "scale"
                to: Enums.splashScreenMetrics.exitContentEndScale
                duration: Enums.duration.splashGridContentFade
                easing.type: Easing.InCubic
            }
            PauseAnimation { duration: Enums.duration.splashExitDissolve }
            SequentialAnimation {
                PauseAnimation {
                    duration: Enums.duration.splashExitDissolve -
                              Enums.duration.splashGridCellFade
                }
                NumberAnimation {
                    target: effect.targetWindow
                    property: "opacity"
                    to: Enums.opacityLevel.invisible
                    duration: Enums.duration.splashGridCellFade
                    easing.type: Easing.InOutCubic
                }
            }
        }
        ScriptAction {
            script: {
                effect._running = false
                effect._dissolving = false
                effect.onCloseCallback()
            }
        }
    }

    Repeater {
        id: dissolveGrid

        model: effect._cellCount

        delegate: Rectangle {
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
            x: effect.targetItem.x + gridCell._column * effect.targetItem.width /
               effect._columns
            y: effect.targetItem.y + gridCell._row * effect.targetItem.height /
               effect._rows
            width: effect.targetItem.width / effect._columns +
                   Enums.splashScreenMetrics.exitGridOverlap
            height: effect.targetItem.height / effect._rows +
                    Enums.splashScreenMetrics.exitGridOverlap
            color: effect.backgroundColor
            opacity: Enums.opacityLevel.visible
            visible: effect._dissolving

            SequentialAnimation on opacity {
                running: effect._dissolving

                PauseAnimation { duration: gridCell._delay }
                NumberAnimation {
                    to: Enums.opacityLevel.invisible
                    duration: Enums.duration.splashGridCellFade
                    easing.type: Easing.InOutCubic
                }
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
        z: Enums.zIndex.controls
        transformOrigin: Item.Center
        sourceItem: effect.targetItem
        hideSource: false
        live: false
        recursive: false
        smooth: true
    }
}
