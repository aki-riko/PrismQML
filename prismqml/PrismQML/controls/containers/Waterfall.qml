// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// Waterfall - Pure QtQuick implementation 瀑布流布局纯QtQuick实现
// Pinterest-like waterfall layout 类似Pinterest瀑布流
Item {
    id: control
    
    property int columns: 2
    property int spacing: Enums.spacing.l
    property var model: []
    property Component delegate: null

    property real contentHeight: {
        var maxH = 0
        for (var i = 0; i < columnHeights.length; i++) {
            if (columnHeights[i] > maxH) maxH = columnHeights[i]
        }
        return maxH
    }
    
    property var columnHeights: {
        var heights = []
        for (var i = 0; i < columns; i++) heights.push(0)
        return heights
    }

    function _relayout() {
        var heights = []
        for (var column = 0; column < columns; column++) heights.push(0)
        for (var itemIndex = 0; itemIndex < itemRepeater.count; itemIndex++) {
            var loader = itemRepeater.itemAt(itemIndex)
            if (!loader || !loader.item) continue
            var targetColumn = 0
            var targetHeight = heights[0] || 0
            for (var candidate = 1; candidate < columns; candidate++) {
                var candidateHeight = heights[candidate] || 0
                if (candidateHeight < targetHeight) {
                    targetHeight = candidateHeight
                    targetColumn = candidate
                }
            }
            loader.targetColumn = targetColumn
            loader.targetY = targetHeight
            heights[targetColumn] = targetHeight + loader.item.height + spacing
        }
        columnHeights = heights
    }

    implicitWidth: 400
    implicitHeight: contentHeight

    onColumnsChanged: Qt.callLater(_relayout)
    onSpacingChanged: Qt.callLater(_relayout)

    Repeater {
        id: itemRepeater

        model: control.model
        onItemRemoved: Qt.callLater(control._relayout)

        Loader {
            id: itemLoader

            property var modelData: control.model[index]
            property int itemIndex: index

            // Find shortest column 找到最短列
            property int targetColumn: -1
            property real targetY: 0

            sourceComponent: control.delegate
            x: targetColumn * ((control.width - (control.columns - 1) * control.spacing) / control.columns + control.spacing)
            y: targetY
            width: (control.width - (control.columns - 1) * control.spacing) / control.columns

            onLoaded: control._relayout()

            Connections {
                function onHeightChanged() {
                    Qt.callLater(control._relayout)
                }

                target: itemLoader.item
            }
        }
    }
    
}
