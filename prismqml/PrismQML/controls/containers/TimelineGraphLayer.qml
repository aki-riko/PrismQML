// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Shapes
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
    property color nodeBackground: Enums.cardColor
    property color selectedColor: Enums.accentColor

    // ==================== Readonly State 只读状态 ====================
    readonly property real _strokeWidth: Enums.border.normal
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
        return Enums.spacing.timelineGraphPadding
            + Enums.spacing.timelineGraphLane / 2
            + safeLane * Enums.spacing.timelineGraphLane
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
            readonly property real middleY: (startY + endY) / 2
            readonly property color segmentColor: control._colorFor((modelData || {}).colorIndex)

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
                color: segmentItem.segmentColor
            }

            Shape {
                anchors.fill: parent
                visible: segmentItem.fromX !== segmentItem.toX
                preferredRendererType: Shape.CurveRenderer

                ShapePath {
                    startX: segmentItem.fromX
                    startY: segmentItem.startY
                    strokeWidth: control._strokeWidth
                    strokeColor: segmentItem.segmentColor
                    fillColor: Enums.transparent
                    capStyle: ShapePath.FlatCap

                    PathCubic {
                        x: segmentItem.toX
                        y: segmentItem.endY
                        control1X: segmentItem.fromX
                        control1Y: segmentItem.middleY
                        control2X: segmentItem.toX
                        control2Y: segmentItem.middleY
                    }
                }
            }
        }
    }

    Rectangle {
        x: control._nodeX - control._nodeOuterRadius
        y: control.nodeY - control._nodeOuterRadius
        width: control._nodeOuterRadius * 2
        height: control._nodeOuterRadius * 2
        radius: control._nodeOuterRadius
        visible: control.showNode
        color: control.nodeBackground

        Rectangle {
            anchors.centerIn: parent
            width: control._nodeRadius * 2
            height: control._nodeRadius * 2
            radius: control._nodeRadius
            color: control._colorFor((control.graphData || {}).nodeColorIndex)
        }
    }

    Rectangle {
        x: control._nodeX - width / 2
        y: control.nodeY - height / 2
        width: (control._nodeOuterRadius + Enums.spacing.xxs) * 2
        height: width
        radius: width / 2
        visible: control.showNode && control.selected
        color: Enums.transparent
        border.width: control._strokeWidth
        border.color: control.selectedColor
    }
}
