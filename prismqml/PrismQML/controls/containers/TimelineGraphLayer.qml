// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// TimelineGraphLayer - Generic per-row graph renderer 通用时间线逐行图渲染器
Item {
    id: control

    // ==================== Required Props 必需属性 ====================
    required property var graphData
    required property bool showNode
    required property real nodeY
    required property bool selected

    // ==================== Public Props 公开属性 ====================
    property var graphPalette: Enums.chartColors.extendedPalette
    property color selectedColor: Enums.accentColor

    // ==================== Readonly State 只读状态 ====================
    readonly property real _strokeWidth: Enums.border.normal
    readonly property real _halfStrokeWidth: _strokeWidth / 2
    readonly property real _curveTerminalLength: Enums.spacing.xs
    readonly property real _devicePixelRatio: Math.max(
        1, DpiManager.devicePixelRatio || 1)
    readonly property int _strokePixelCount: Math.max(
        1, Math.round(_strokeWidth * _devicePixelRatio))
    readonly property real _nodeRadius: Enums.controlSize.timelineGraphNode / 2
    readonly property real _nodeOuterRadius: _nodeRadius + _strokeWidth
    readonly property real _nodeX: _laneX((graphData || {}).nodeLane)
    readonly property var _segments: _normalizeSegments(graphData && graphData.segments)

    // ==================== Internal Methods 内部方法 ====================
    function _normalizeSegments(value) {
        if (!value || typeof value.length !== "number") return []
        var result = []
        for (var i = 0; i < value.length; i++) {
            result.push(value[i] && typeof value[i] === "object" ? value[i] : {})
        }
        return result
    }

    function _laneX(lane) {
        var safeLane = Math.max(0, Number(lane) || 0)
        var laneCenter = Enums.spacing.timelineGraphPadding
            + Enums.spacing.timelineGraphLane / 2
            + safeLane * Enums.spacing.timelineGraphLane
        // Center odd-pixel strokes on physical half-pixels. 奇数物理像素描边对齐半像素中心。
        var physicalPhase = control._strokePixelCount % 2 === 0 ? 0 : 0.5
        return (Math.round(laneCenter * control._devicePixelRatio - physicalPhase)
            + physicalPhase) / control._devicePixelRatio
    }

    function _colorFor(index) {
        if (!graphPalette || graphPalette.length === 0) return Enums.accentColor
        var safeIndex = Math.abs(Math.floor(Number(index) || 0)) % graphPalette.length
        return graphPalette[safeIndex]
    }

    objectName: "timelineGraphLayer"

    // ==================== Content 内容 ====================
    Repeater {
        model: control._segments

        delegate: Item {
            id: segmentItem

            required property var modelData
            readonly property real fromX: control._laneX((modelData || {}).fromLane)
            readonly property real toX: control._laneX((modelData || {}).toLane)
            readonly property real startY: (modelData || {}).startAtNode ? control.nodeY : 0
            readonly property real endY: (modelData || {}).endAtNode ? control.nodeY : height
            readonly property real terminalLength: Math.min(
                control._curveTerminalLength, Math.max(0, (endY - startY) / 4))
            readonly property real curveStartY: startY
                + ((modelData || {}).startAtNode ? 0 : terminalLength)
            readonly property real curveEndY: endY
                - ((modelData || {}).endAtNode ? 0 : terminalLength)
            readonly property real curveMiddleY: (curveStartY + curveEndY) / 2
            readonly property color segmentColor: control._colorFor((modelData || {}).colorIndex)
            readonly property color paintColor: control.selected
                ? control.selectedColor : segmentColor

            function _paintCurve(ctx, pathFromX, pathToX, pathStartY,
                    pathEndY, pathMiddleY, pathColor) {
                ctx.clearRect(0, 0, width, height)
                ctx.beginPath()
                ctx.moveTo(pathFromX, pathStartY)
                ctx.bezierCurveTo(
                    pathFromX, pathMiddleY, pathToX, pathMiddleY, pathToX, pathEndY)
                ctx.lineWidth = control._strokeWidth
                ctx.lineCap = "butt"
                ctx.lineJoin = "round"
                ctx.strokeStyle = pathColor
                ctx.stroke()
            }

            width: control.width
            height: control.height

            // Scene-graph rectangles tile exactly at virtual row boundaries.
            // 场景图矩形在虚拟行边界精确拼接，避免 Canvas 纹理重复混合。
            Rectangle {
                x: segmentItem.fromX - control._strokeWidth / 2
                y: segmentItem.startY
                width: control._strokeWidth
                height: Math.max(0, segmentItem.endY - segmentItem.startY)
                visible: segmentItem.fromX === segmentItem.toX
                color: segmentItem.paintColor
            }

            Canvas {
                id: canvas
                property real pathFromX: segmentItem.fromX
                property real pathToX: segmentItem.toX
                property real pathStartY: segmentItem.curveStartY
                property real pathEndY: segmentItem.curveEndY
                property real pathMiddleY: segmentItem.curveMiddleY
                property color pathColor: segmentItem.paintColor

                anchors.fill: parent
                visible: segmentItem.fromX !== segmentItem.toX
                antialiasing: true
                onPaint: segmentItem._paintCurve(
                    getContext("2d"), pathFromX, pathToX, pathStartY,
                    pathEndY, pathMiddleY, pathColor)
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
                onVisibleChanged: if (visible) requestPaint()
                onPathFromXChanged: requestPaint()
                onPathToXChanged: requestPaint()
                onPathStartYChanged: requestPaint()
                onPathEndYChanged: requestPaint()
                onPathMiddleYChanged: requestPaint()
                onPathColorChanged: requestPaint()
            }

            Rectangle {
                x: segmentItem.fromX - control._halfStrokeWidth
                y: segmentItem.startY
                width: control._strokeWidth
                height: segmentItem.curveStartY - segmentItem.startY
                visible: segmentItem.fromX !== segmentItem.toX && height > 0
                color: segmentItem.paintColor
            }

            Rectangle {
                x: segmentItem.toX - control._halfStrokeWidth
                y: segmentItem.curveEndY
                width: control._strokeWidth
                height: segmentItem.endY - segmentItem.curveEndY
                visible: segmentItem.fromX !== segmentItem.toX && height > 0
                color: segmentItem.paintColor
            }
        }
    }

    Rectangle {
        x: control._nodeX - control._nodeRadius
        y: control.nodeY - control._nodeRadius
        width: control._nodeRadius * 2
        height: control._nodeRadius * 2
        radius: control._nodeRadius
        visible: control.showNode
        color: control.selected ? control.selectedColor
            : control._colorFor((control.graphData || {}).nodeColorIndex)
    }

    Rectangle {
        objectName: "timelineGraphSelectionRing"
        x: control._nodeX - width / 2
        y: control.nodeY - height / 2
        width: (control._nodeOuterRadius + Enums.spacing.xxs) * 2
        height: width
        radius: width / 2
        visible: control.showNode
        color: Enums.transparent
        border.width: Enums.border.thick
        border.color: control.selectedColor
        opacity: control.selected ? 1 : 0
        scale: control.selected ? 1 : 0.7
        transformOrigin: Item.Center
        Behavior on opacity {
            OpacityAnimator { duration: Enums.duration.fast }
        }
        Behavior on scale {
            ScaleAnimator {
                duration: Enums.duration.fast
                easing.type: Easing.OutCubic
            }
        }
    }
}
