// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
    
    implicitWidth: 400
    implicitHeight: contentHeight
    
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
    
    Repeater {
        model: control.model
        
        Loader {
            id: itemLoader
            sourceComponent: control.delegate
            
            property var modelData: control.model[index]
            property int itemIndex: index
            
            // Find shortest column 找到最短列
            property int targetColumn: {
                var minCol = 0
                var minH = control.columnHeights[0] || 0
                for (var i = 1; i < control.columns; i++) {
                    var h = control.columnHeights[i] || 0
                    if (h < minH) {
                        minH = h
                        minCol = i
                    }
                }
                return minCol
            }
            
            x: targetColumn * ((control.width - (control.columns - 1) * control.spacing) / control.columns + control.spacing)
            y: control.columnHeights[targetColumn] || 0
            width: (control.width - (control.columns - 1) * control.spacing) / control.columns
            
            onLoaded: {
                // Update column height 更新列高度
                if (item) {
                    var newHeights = control.columnHeights.slice()
                    newHeights[targetColumn] = (newHeights[targetColumn] || 0) + item.height + control.spacing
                    control.columnHeights = newHeights
                }
            }
        }
    }
    
}
