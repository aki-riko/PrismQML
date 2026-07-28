// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../.."
import QtQuick  // Keep native types unprefixed after library import 库导入后保留原生类型无前缀

// QMLPage - Reusable QML loading page with SplashScreen exit 可复用 SplashScreen 退场效果的 QML 加载页
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string text: { Translator._v; return Translator.tr("loading") }  // Loading message 加载提示
    property bool running: visible                  // Run animation while loading 加载时运行动画
    property color backgroundColor: Enums.backgroundColor  // Page background 页面背景

    // ==================== Internal Props 内部属性 ====================
    readonly property bool finishing: _finishing     // Exit is running 正在退场
    property bool _finishing: false

    // ==================== Signals 信号 ====================
    signal finished()  // Emitted after the page is removed 页面移除后触发

    // ==================== Public Methods 公开方法 ====================
    function start() {
        exitDissolveAnim.stop()
        control._finishing = false
        control.visible = true
        contentColumn.opacity = Enums.opacityLevel.visible
        contentColumn.scale = Enums.opacityLevel.visible
        for (var i = 0; i < dissolveGrid.count; i++) {
            var cell = dissolveGrid.itemAt(i)
            if (cell) cell.opacity = Enums.opacityLevel.visible
        }
    }

    function finish() {
        if (control._finishing || !control.visible) return
        control._finishing = true
        exitDissolveAnim.start()
    }

    color: Enums.transparent
    clip: true

    // Grid permeation dissolve animation 网格渗透溶解动画
    SequentialAnimation {
        id: exitDissolveAnim

        ParallelAnimation {
            NumberAnimation {
                target: contentColumn
                property: "opacity"
                to: Enums.opacityLevel.invisible
                duration: Enums.duration.splashGridContentFade
                easing.type: Easing.InCubic
            }

            NumberAnimation {
                target: contentColumn
                property: "scale"
                to: Enums.splashScreenMetrics.exitContentEndScale
                duration: Enums.duration.splashGridContentFade
                easing.type: Easing.InCubic
            }

            PauseAnimation { duration: Enums.duration.splashExitDissolve }
        }

        ScriptAction {
            script: {
                control.visible = false
                control.finished()
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
            x: gridCell._column * control.width / Enums.splashScreenMetrics.exitGridColumns
            y: gridCell._row * control.height / Enums.splashScreenMetrics.exitGridRows
            width: control.width / Enums.splashScreenMetrics.exitGridColumns +
                   Enums.splashScreenMetrics.exitGridOverlap
            height: control.height / Enums.splashScreenMetrics.exitGridRows +
                    Enums.splashScreenMetrics.exitGridOverlap
            color: control.backgroundColor
            opacity: Enums.opacityLevel.visible

            SequentialAnimation on opacity {
                running: control._finishing

                PauseAnimation { duration: gridCell._delay }
                NumberAnimation {
                    to: Enums.opacityLevel.invisible
                    duration: Enums.duration.splashGridCellFade
                    easing.type: Easing.InOutCubic
                }
            }
        }
    }

    // ==================== Content 内容 ====================
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
