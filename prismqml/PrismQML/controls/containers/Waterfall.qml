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
    property bool _appendLayoutPending: false
    property bool _layoutAppendable: true
    property int _relayoutCount: 0
    property int _laidOutItemCount: 0

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
    function _invalidateLayout() {
        _laidOutItemCount = 0
        _layoutAppendable = false
        _scheduleRelayout()
    }

    function _scheduleRelayout() {
        if (_relayoutPending) return
        _relayoutPending = true
        Qt.callLater(function() {
            _relayoutPending = false
            _relayout()
        })
    }

    function _scheduleAppendLayout() {
        if (_appendLayoutPending || _relayoutPending) return
        if (!_layoutAppendable) {
            _scheduleRelayout()
            return
        }
        _appendLayoutPending = true
        Qt.callLater(function() {
            _appendLayoutPending = false
            _appendLoadedItems()
        })
    }

    function _placeLoader(loader, heights) {
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

    function _appendLoadedItems() {
        if (_relayoutPending || !_layoutAppendable
                || columnHeights.length !== _safeColumns) return
        var heights = columnHeights.slice(0)
        var itemIndex = _laidOutItemCount
        while (itemIndex < itemRepeater.count) {
            var loader = itemRepeater.itemAt(itemIndex)
            if (!loader || !loader.item) break
            _placeLoader(loader, heights)
            itemIndex++
        }
        if (itemIndex === _laidOutItemCount) return
        _laidOutItemCount = itemIndex
        columnHeights = heights
    }

    function _relayout() {
        _relayoutCount++
        var heights = []
        for (var column = 0; column < _safeColumns; column++) heights.push(0)
        var complete = true
        for (var itemIndex = 0; itemIndex < itemRepeater.count; itemIndex++) {
            var loader = itemRepeater.itemAt(itemIndex)
            if (!loader || !loader.item) {
                complete = false
                continue
            }
            _placeLoader(loader, heights)
        }
        _layoutAppendable = complete
        _laidOutItemCount = complete ? itemRepeater.count : 0
        columnHeights = heights
    }

    implicitWidth: 400
    implicitHeight: contentHeight

    onColumnsChanged: _invalidateLayout()
    onDelegateChanged: _invalidateLayout()
    onSpacingChanged: _invalidateLayout()

    Repeater {
        id: itemRepeater

        model: control.model
        onItemAdded: function(index, item) {
            if (index < control._laidOutItemCount) control._invalidateLayout()
        }
        onItemRemoved: control._invalidateLayout()

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

            onLoaded: control._scheduleAppendLayout()

            Connections {
                function onHeightChanged() {
                    if (itemLoader.itemIndex < control._laidOutItemCount) {
                        control._invalidateLayout()
                    }
                }

                target: itemLoader.item
            }
        }
    }
    
}
