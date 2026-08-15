// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data/Label"

// BarChartBar - Single-series bar delegate 单系列柱体委托
// Keeps vertical and horizontal bar visuals in one reusable delegate 将垂直与水平柱体视觉统一到可复用委托
Item {
    id: control

    // ==================== Required Props 必需属性 ====================
    required property var chart
    required property bool horizontal
    required property int index
    required property var modelData

    // ==================== Readonly State 只读状态 ====================
    readonly property bool hovered: chart.hoveredIndex === index
    readonly property real barValue: modelData && modelData.value !== undefined ? modelData.value : 0
    readonly property bool isPositiveValue: chart.isPositive(barValue)
    readonly property real barRatio: chart.getBarRatio(barValue)
    readonly property real zeroY: chart.zeroLineRatio * height
    readonly property real zeroX: {
        var range = chart.valueRange
        if (!range.hasNegative) return 0
        if (!range.hasPositive) return width
        return Math.abs(range.min) / (range.max - range.min) * width
    }
    readonly property color barColor: chart.getColor(index)

    // ==================== Signals 信号 ====================
    signal barHovered(int index)
    signal barClicked(int index, var data)

    // ==================== Size 尺寸 ====================
    width: horizontal
        ? parent.width
        : (parent.width - parent.spacing * (chart.chartData.length - 1))
            / Math.max(chart.chartData.length, 1)
    height: horizontal
        ? (parent.height - parent.spacing * (chart.chartData.length - 1))
            / Math.max(chart.chartData.length, 1)
        : parent.height

    // ==================== Content 内容 ====================
    Canvas {
        id: barCanvas

        property color barColor: control.barColor
        property bool barHovered: control.hovered
        property bool isPositive: control.isPositiveValue

        anchors.horizontalCenter: control.horizontal ? undefined : parent.horizontalCenter
        anchors.verticalCenter: control.horizontal ? parent.verticalCenter : undefined
        width: control.horizontal
            ? (control.chart.animated ? 0 : control.barRatio * parent.width)
            : Math.min(parent.width * 0.7, Enums.spacing.xxxl)
        height: control.horizontal
            ? Math.min(parent.height * 0.7, Enums.spacing.xxl)
            : (control.chart.animated ? 0 : control.barRatio * parent.height)
        x: control.horizontal
            ? (control.isPositiveValue ? control.zeroX : control.zeroX - width)
            : 0
        y: control.horizontal
            ? 0
            : (control.isPositiveValue ? control.zeroY - height : control.zeroY)

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            if (width <= 0 || height <= 0) return

            var r = Math.min(Enums.radius.small, width / 2, height / 2)
            var color = barHovered ? Qt.lighter(control.barColor, 1.1) : control.barColor

            if (!control.horizontal) {
                ctx.fillStyle = color
                ctx.beginPath()
                ctx.moveTo(r, 0)
                ctx.lineTo(width - r, 0)
                ctx.arcTo(width, 0, width, r, r)
                ctx.lineTo(width, height)
                ctx.lineTo(0, height)
                ctx.lineTo(0, r)
                ctx.arcTo(0, 0, r, 0, r)
                ctx.closePath()
                ctx.fill()
                return
            }

            var gradient = ctx.createLinearGradient(0, 0, width, 0)
            if (isPositive) {
                gradient.addColorStop(0, barHovered ? Qt.lighter(control.barColor, 1.05) : control.barColor)
                gradient.addColorStop(1, barHovered ? Qt.lighter(control.barColor, 1.2) : Qt.lighter(control.barColor, 1.1))
            } else {
                gradient.addColorStop(0, barHovered ? Qt.lighter(control.barColor, 1.2) : Qt.lighter(control.barColor, 1.1))
                gradient.addColorStop(1, barHovered ? Qt.lighter(control.barColor, 1.05) : control.barColor)
            }
            ctx.fillStyle = gradient
            ctx.beginPath()
            if (isPositive) {
                ctx.moveTo(0, 0)
                ctx.lineTo(width - r, 0)
                ctx.arcTo(width, 0, width, r, r)
                ctx.lineTo(width, height - r)
                ctx.arcTo(width, height, width - r, height, r)
                ctx.lineTo(0, height)
                ctx.closePath()
            } else {
                ctx.moveTo(r, 0)
                ctx.lineTo(width, 0)
                ctx.lineTo(width, height)
                ctx.lineTo(r, height)
                ctx.arcTo(0, height, 0, height - r, r)
                ctx.lineTo(0, r)
                ctx.arcTo(0, 0, r, 0, r)
                ctx.closePath()
            }
            ctx.fill()
        }

        onBarColorChanged: requestPaint()
        onBarHoveredChanged: requestPaint()
        onHeightChanged: if (!control.horizontal) requestPaint()
        onWidthChanged: if (control.horizontal) requestPaint()

        Behavior on height {
            enabled: control.chart.animated && !control.horizontal
            NumberAnimation { duration: Enums.duration.slow; easing.type: Easing.OutQuint }
        }

        Behavior on width {
            enabled: control.chart.animated && control.horizontal
            NumberAnimation { duration: Enums.duration.slow; easing.type: Easing.OutQuint }
        }

        Component.onCompleted: {
            if (!control.chart.animated) return
            if (control.horizontal) {
                Qt.callLater(function() {
                    barCanvas.width = control.barRatio * control.width
                })
            } else {
                height = control.barRatio * control.height
            }
        }
    }

    Label {
        type: Enums.label.type_caption
        anchors.horizontalCenter: control.horizontal ? undefined : parent.horizontalCenter
        anchors.verticalCenter: control.horizontal ? parent.verticalCenter : undefined
        x: control.horizontal
            ? (control.isPositiveValue
                ? barCanvas.x + barCanvas.width + Enums.spacing.xs
                : barCanvas.x - width - Enums.spacing.xs)
            : 0
        y: control.horizontal
            ? 0
            : (control.isPositiveValue
                ? barCanvas.y - height - Enums.spacing.xs
                : barCanvas.y + barCanvas.height + Enums.spacing.xs)
        text: control.barValue
        font.weight: control.hovered ? Font.DemiBold : Font.Normal
        color: control.hovered ? Enums.textColor.primary : Enums.textColor.secondary
        visible: control.chart.showValues

        HoverBehavior on color {
            active: control.hovered
            enterDuration: Enums.duration.fast
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: control.barHovered(control.index)
        onExited: control.barHovered(-1)
        onClicked: control.barClicked(control.index, control.modelData)
    }
}
