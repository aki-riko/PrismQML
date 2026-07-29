// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../data/Label"

// ChartEmptyState - Shared no-data presentation 图表空数据状态
Column {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var chart: null

    // ==================== Readonly State 只读状态 ====================
    readonly property string _defaultText: {
        Translator._v
        return Translator.tr("no_data")
    }

    anchors.centerIn: parent
    spacing: Enums.spacing.m
    visible: chart && (
        (chart._isXYChart && !chart._isScatter
            && !chart._hasChartData && !chart._hasSeriesValues)
        || (chart._isScatter && !chart._hasScatterData)
        || (chart._isPie && !chart._hasChartData)
        || (chart._isRadar && !chart._hasRadarData)
        || (chart._isBoxplot && !chart._hasBoxplotData))
    opacity: visible ? 1.0 : 0.0

    Label {
        type: Enums.label.type_display
        anchors.horizontalCenter: parent.horizontalCenter
        text: "📊"
        font.pixelSize: Enums.typography.displayLarge
        color: Enums.textColor.tertiary

        SequentialAnimation on y {
            objectName: "emptyStateAnimation"
            running: control.visible
            loops: Animation.Infinite

            NumberAnimation {
                from: 0
                to: -Enums.spacing.xs
                duration: Enums.duration.emptyFloat
                easing.type: Easing.InOutSine
            }

            NumberAnimation {
                from: -Enums.spacing.xs
                to: 0
                duration: Enums.duration.emptyFloat
                easing.type: Easing.InOutSine
            }
        }
    }

    Label {
        type: Enums.label.type_body
        anchors.horizontalCenter: parent.horizontalCenter
        text: chart && chart.emptyText ? chart.emptyText : control._defaultText
        color: Enums.textColor.tertiary
    }

    Behavior on opacity {
        NumberAnimation {
            duration: Enums.duration.medium
            easing.type: Easing.OutCubic
        }
    }
}
