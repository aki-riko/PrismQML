// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// QMLPageExitDissolve - On-demand loading-page exit effect 按需加载页退场效果
Item {
    id: effect

    // ==================== Required Props 必需属性 ====================
    required property Item contentItem
    required property color cellColor

    // ==================== Internal Props 内部属性 ====================
    property bool _running: false

    // ==================== Signals 信号 ====================
    signal finished()

    // ==================== Public Methods 公开方法 ====================
    function start() {
        if (effect._running) return
        effect._running = true
        exitDissolveAnim.start()
    }

    visible: _running

    // Grid permeation dissolve animation 网格渗透溶解动画
    SequentialAnimation {
        id: exitDissolveAnim

        ParallelAnimation {
            NumberAnimation {
                target: effect.contentItem
                property: "opacity"
                to: Enums.opacityLevel.invisible
                duration: Enums.duration.splashGridContentFade
                easing.type: Easing.InCubic
            }

            NumberAnimation {
                target: effect.contentItem
                property: "scale"
                to: Enums.splashScreenMetrics.exitContentEndScale
                duration: Enums.duration.splashGridContentFade
                easing.type: Easing.InCubic
            }

            PauseAnimation { duration: Enums.duration.splashExitDissolve }
        }

        ScriptAction {
            script: {
                effect._running = false
                effect.finished()
            }
        }
    }

    // Seamless cells reveal the loaded content center-out 无缝网格块由中心向外揭露已加载内容
    Repeater {
        id: dissolveGrid

        model: Enums.splashScreenMetrics.exitGridColumns *
               Enums.splashScreenMetrics.exitGridRows

        delegate: Rectangle {
            id: gridCell

            readonly property int _column: index % Enums.splashScreenMetrics.exitGridColumns
            readonly property int _row: Math.floor(index / Enums.splashScreenMetrics.exitGridColumns)
            readonly property real _centerColumn: (Enums.splashScreenMetrics.exitGridColumns - 1) / 2
            readonly property real _centerRow: (Enums.splashScreenMetrics.exitGridRows - 1) / 2
            readonly property int _delay: Math.round((
                Math.abs(gridCell._column - gridCell._centerColumn) +
                Math.abs(gridCell._row - gridCell._centerRow)
            ) * Enums.duration.splashGridDelayStep)

            objectName: "qmlPageGridCell_" + index
            x: gridCell._column * effect.width / Enums.splashScreenMetrics.exitGridColumns
            y: gridCell._row * effect.height / Enums.splashScreenMetrics.exitGridRows
            width: effect.width / Enums.splashScreenMetrics.exitGridColumns +
                   Enums.splashScreenMetrics.exitGridOverlap
            height: effect.height / Enums.splashScreenMetrics.exitGridRows +
                    Enums.splashScreenMetrics.exitGridOverlap
            color: effect.cellColor
            opacity: Enums.opacityLevel.visible

            SequentialAnimation on opacity {
                running: effect._running

                PauseAnimation { duration: gridCell._delay }
                NumberAnimation {
                    to: Enums.opacityLevel.invisible
                    duration: Enums.duration.splashGridCellFade
                    easing.type: Easing.InOutCubic
                }
            }
        }
    }
}
