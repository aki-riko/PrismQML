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

    // ==================== Internal Props 内部属性 ====================
    property bool _relayoutPending: false
    property int _relayoutCount: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property int _safeColumns: Math.max(1, columns)

    property real contentHeight: {
        var maxH = 0
        for (var i = 0; i < columnHeights.length; i++) {
            if (columnHeights[i] > maxH) maxH = columnHeights[i]
        }
        return maxH
    }
    
    property var columnHeights: {
        var heights = []
        for (var i = 0; i < _safeColumns; i++) heights.push(0)
        return heights
    }

    // ==================== Internal Methods 内部方法 ====================
    function _scheduleRelayout() {
        if (_relayoutPending) return
        _relayoutPending = true
        Qt.callLater(function() {
            _relayoutPending = false
            _relayout()
        })
    }

    function _relayout() {
        _relayoutCount++
        var heights = []
        for (var column = 0; column < _safeColumns; column++) heights.push(0)
        for (var itemIndex = 0; itemIndex < itemRepeater.count; itemIndex++) {
            var loader = itemRepeater.itemAt(itemIndex)
            if (!loader || !loader.item) continue
            var targetColumn = 0
            var targetHeight = heights[0] || 0
            for (var candidate = 1; candidate < _safeColumns; candidate++) {
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

    onColumnsChanged: _scheduleRelayout()
    onSpacingChanged: _scheduleRelayout()

    Repeater {
        id: itemRepeater

        model: control.model
        onItemRemoved: control._scheduleRelayout()

        Loader {
            id: itemLoader

            property var modelData: control.model[index]
            property int itemIndex: index

            // Find shortest column 找到最短列
            property int targetColumn: -1
            property real targetY: 0

            sourceComponent: control.delegate
            x: targetColumn * ((control.width - (control._safeColumns - 1) * control.spacing) / control._safeColumns + control.spacing)
            y: targetY
            width: (control.width - (control._safeColumns - 1) * control.spacing) / control._safeColumns

            onLoaded: control._scheduleRelayout()

            Connections {
                function onHeightChanged() {
                    control._scheduleRelayout()
                }

                target: itemLoader.item
            }
        }
    }
    
}
