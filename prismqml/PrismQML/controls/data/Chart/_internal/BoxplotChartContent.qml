// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "BoxplotChartGeometry.js" as Geometry

// BoxplotChartContent - Boxplot chart rendering component 箱线图渲染组件
// Fluent Design style: clean boxes with subtle hover effects
// Fluent Design 风格：简洁箱体+微妙悬停效果

Item {
    id: root
    
    // ==================== Required Props 必需属性 ====================
    // boxplotData format 数据格式:
    // [{
    //     label: "Category",
    //     min: 10,        // Lower whisker 下须
    //     q1: 25,         // First quartile 第一四分位数
    //     median: 50,     // Median 中位数
    //     q3: 75,         // Third quartile 第三四分位数
    //     max: 90,        // Upper whisker 上须
    //     outliers: [5, 95, 100]  // Optional outliers 可选异常点
    // }, ...]
    required property var boxplotData
    required property bool animated
    required property bool showValues
    required property bool isHorizontal    // Horizontal or vertical 水平或垂直
    
    // ==================== Public Props 公开属性 ====================
    property int hoveredIndex: -1
    property color boxColor: Enums.accentColor

    // ==================== Internal Props 内部属性 ====================
    property var _boxGeometry: []
    property bool _boxGeometryDirty: true
    property int _boxGeometryBuildCount: 0
    property int _lastFramePointUpdateCount: 0
    property real _boxGeometryGroupSize: 0
    property real _boxGeometrySize: 0
    property real _lastGeometryProgress: -1
    property int _lastFrameBoxDrawCount: 0
    property int _paintedHoverIndex: -1

    // ==================== Readonly State 只读状态 ====================
    readonly property int dataLength: boxplotData.length
    readonly property var valueRange: {
        var min = Infinity, max = -Infinity
        for (var i = 0; i < boxplotData.length; i++) {
            var d = boxplotData[i]
            if (!d || typeof d.min !== "number" || typeof d.q1 !== "number" ||
                    typeof d.median !== "number" || typeof d.q3 !== "number" ||
                    typeof d.max !== "number" || !isFinite(d.min) || !isFinite(d.q1) ||
                    !isFinite(d.median) || !isFinite(d.q3) || !isFinite(d.max)) continue
            if (d.min < min) min = d.min
            if (d.max > max) max = d.max
            // Check outliers 检查异常点
            var outliers = d.outliers || []
            for (var j = 0; j < outliers.length; j++) {
                if (typeof outliers[j] !== "number" || !isFinite(outliers[j])) continue
                if (outliers[j] < min) min = outliers[j]
                if (outliers[j] > max) max = outliers[j]
            }
        }
        if (!isFinite(min) || !isFinite(max)) return { min: 0, max: 1 }
        var padding = (max - min) * 0.1 || 1
        return { min: min - padding, max: max + padding }
    }

    // ==================== Signals 信号 ====================
    signal boxClicked(int index, var data)
    signal boxHovered(int index)

    // ==================== Internal Methods 内部方法 ====================
    function valueToPosition(value) {
        var range = valueRange.max - valueRange.min
        if (range === 0) return isHorizontal ? width / 2 : height / 2
        var ratio = (value - valueRange.min) / range
        return isHorizontal ? ratio * width : height - ratio * height
    }
    
    function getBoxColor(index) {
        if (boxplotData[index] && boxplotData[index].color) return boxplotData[index].color
        return Enums.chartColors.extendedPalette[index % Enums.chartColors.extendedPalette.length]
    }

    function _isValidBoxplot(item) {
        return item && typeof item.min === "number" && typeof item.q1 === "number" &&
               typeof item.median === "number" && typeof item.q3 === "number" &&
               typeof item.max === "number" && isFinite(item.min) && isFinite(item.q1) &&
               isFinite(item.median) && isFinite(item.q3) && isFinite(item.max)
    }

    function _buildBoxGeometryItem(index) {
        var item = boxplotData[index]
        if (!_isValidBoxplot(item)) return null
        var outlierFinalPositions = []
        var outlierPositions = []
        var outliers = item.outliers || []
        for (var outlierIndex = 0; outlierIndex < outliers.length; outlierIndex++) {
            outlierFinalPositions.push(valueToPosition(outliers[outlierIndex]))
            outlierPositions.push(0)
        }
        return {
            center: (index + 0.5) * _boxGeometryGroupSize,
            minFinal: valueToPosition(item.min), q1Final: valueToPosition(item.q1),
            medianFinal: valueToPosition(item.median), q3Final: valueToPosition(item.q3),
            maxFinal: valueToPosition(item.max),
            minPosition: 0, q1Position: 0, medianPosition: 0,
            q3Position: 0, maxPosition: 0,
            outlierFinalPositions: outlierFinalPositions,
            outlierPositions: outlierPositions
        }
    }

    function _rebuildBoxGeometry(canvasWidth, canvasHeight) {
        var dataLen = dataLength
        var crossSize = isHorizontal ? canvasHeight : canvasWidth
        _boxGeometryGroupSize = dataLen > 0 ? crossSize / dataLen : 0
        _boxGeometrySize = Math.min(_boxGeometryGroupSize * 0.6, Enums.spacing.xxxl * 2)
        var geometry = []
        for (var index = 0; index < dataLen; index++) {
            geometry.push(_buildBoxGeometryItem(index))
        }
        _boxGeometry = geometry
        _boxGeometryDirty = false
        _lastGeometryProgress = -1
        _boxGeometryBuildCount++
    }

    function _updateBoxGeometryItem(geometry, progress, baseline) {
        geometry.minPosition = geometry.minFinal * progress + baseline
        geometry.q1Position = geometry.q1Final * progress + baseline
        geometry.medianPosition = geometry.medianFinal * progress + baseline
        geometry.q3Position = geometry.q3Final * progress + baseline
        geometry.maxPosition = geometry.maxFinal * progress + baseline
        for (var index = 0; index < geometry.outlierFinalPositions.length; index++) {
            geometry.outlierPositions[index] = geometry.outlierFinalPositions[index] * progress + baseline
        }
        return 5 + geometry.outlierFinalPositions.length
    }

    function _updateAnimatedGeometry(progress) {
        if (_boxGeometryDirty) _rebuildBoxGeometry(width, height)
        if (progress === _lastGeometryProgress) {
            _lastFramePointUpdateCount = 0
            return
        }
        var baseline = isHorizontal ? 0 : height * (1 - progress)
        var updateCount = 0
        for (var index = 0; index < _boxGeometry.length; index++) {
            var geometry = _boxGeometry[index]
            if (geometry) updateCount += _updateBoxGeometryItem(geometry, progress, baseline)
        }
        _lastFramePointUpdateCount = updateCount
        _lastGeometryProgress = progress
    }

    function _invalidateBoxGeometry() {
        _boxGeometryDirty = true
        canvas.requestPaint()
    }

    function _hoverDirtyRect(index) {
        return Geometry.dirtyRect(
            index, dataLength, isHorizontal, width, height,
            Enums.spacing.xs + Enums.border.thin
        )
    }

    function _requestHoverPaint() {
        if (_boxGeometryDirty || (animated && canvas.animProgress < 1) ||
                (showValues && !isHorizontal)) {
            canvas.requestPaint()
            return
        }
        var previous = _hoverDirtyRect(_paintedHoverIndex)
        var current = _hoverDirtyRect(hoveredIndex)
        if (!previous && !current) return
        var dirty = Geometry.unitedBounds(previous, current)
        canvas.markDirty(Qt.rect(dirty.x, dirty.y, dirty.width, dirty.height))
    }

    onHoveredIndexChanged: _requestHoverPaint()
    onBoxplotDataChanged: _invalidateBoxGeometry()
    onIsHorizontalChanged: _invalidateBoxGeometry()

    // ==================== Content 内容 ====================
    BoxplotChartCanvas {
        id: canvas

        boxplotControl: root
    }

    // Mouse area 鼠标区域
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.hoveredIndex >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        
        onPositionChanged: (mouse) => {
            var dataLen = root.dataLength
            if (dataLen === 0) return
            
            var foundIndex = -1
            
            if (root.isHorizontal) {
                var groupHeight = height / dataLen
                foundIndex = Math.floor(mouse.y / groupHeight)
            } else {
                var groupWidth = width / dataLen
                foundIndex = Math.floor(mouse.x / groupWidth)
            }
            
            if (foundIndex >= 0 && foundIndex < dataLen) {
                root.boxHovered(foundIndex)
            } else {
                root.boxHovered(-1)
            }
        }
        
        onExited: root.boxHovered(-1)
        
        onClicked: {
            if (root.hoveredIndex >= 0) {
                root.boxClicked(root.hoveredIndex, root.boxplotData[root.hoveredIndex])
            }
        }
    }
}
