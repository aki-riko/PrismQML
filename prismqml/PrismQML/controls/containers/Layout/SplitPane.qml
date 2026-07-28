// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// SplitPane - Pure QtQuick implementation 分割器纯QtQuick实现
// Resizable two-panel split 可拖拽调整大小的两面板
Item {
    id: control
    
    // Size priority system 尺寸优先级系统
    // Compatible with Widget.qml size system 与Widget.qml尺寸系统兼容
    property real preferredWidth: 0
    property real preferredHeight: 0

    // ==================== Public Props 公开属性 ====================
    property int orientation: Qt.Horizontal  // Qt.Horizontal or Qt.Vertical
    property real splitPosition: 0.5  // 0-1 range
    property int handleWidth: Enums.comboBoxMetrics.scrollBarWidth
    property real firstMinimumSize: Enums.controlSize.splitPaneMinimumSize
    property real secondMinimumSize: Enums.controlSize.splitPaneMinimumSize
    
    // Content areas 内容区域
    property alias firstContent: firstPane.data
    property alias secondContent: secondPane.data
    
    // ==================== Readonly State 只读状态 ====================
    readonly property bool isHorizontal: orientation === Qt.Horizontal
    readonly property real _axisSize: Math.max(0, isHorizontal ? width : height)
    readonly property real _safeHandleWidth: Math.min(
        _axisSize,
        Math.max(0, handleWidth)
    )
    readonly property real _availableSize: Math.max(0, _axisSize - _safeHandleWidth)
    readonly property real _effectiveSplitPosition: _boundedSplitPosition(splitPosition)
    readonly property real _firstExtent: _availableSize * _effectiveSplitPosition
    readonly property real _secondExtent: Math.max(0, _availableSize - _firstExtent)
    readonly property color _splitHandleColor: handleArea.pressed
        ? Enums.stateColor.controlBgPressed
        : (handleArea.containsMouse ? Enums.stateColor.controlBgHover
                                    : Enums.stateColor.controlBgTransparent)
    readonly property color _splitGripColor: handleArea.pressed
        ? Enums.stateColor.indicatorActive
        : (handleArea.containsMouse ? Enums.stateColor.indicatorHover
                                    : Enums.stateColor.indicator)

    // ==================== Public Methods 公开方法 ====================
    // Get child count 获取子组件数量
    function count() { return 2 }

    // Clamp a requested split against asymmetric minimum extents.
    // 根据两侧独立最小范围约束请求的分割位置。
    function _boundedSplitPosition(candidate) {
        var safeCandidate = isFinite(candidate) ? candidate : 0.5
        if (_availableSize <= 0)
            return Math.max(0, Math.min(1, safeCandidate))

        var firstMinimum = isFinite(firstMinimumSize)
            ? Math.max(0, firstMinimumSize) : 0
        var secondMinimum = isFinite(secondMinimumSize)
            ? Math.max(0, secondMinimumSize) : 0
        var minimumTotal = firstMinimum + secondMinimum
        if (minimumTotal > _availableSize)
            return minimumTotal > 0 ? firstMinimum / minimumTotal : 0.5

        var minimumPosition = firstMinimum / _availableSize
        var maximumPosition = 1 - secondMinimum / _availableSize
        return Math.max(minimumPosition, Math.min(maximumPosition, safeCandidate))
    }

    // Keep writable public state aligned with the safe rendered geometry.
    // 让可写公开状态与安全渲染几何保持一致。
    function _clampSplitPosition() {
        var boundedPosition = _boundedSplitPosition(splitPosition)
        if (!isFinite(splitPosition)
                || Math.abs(splitPosition - boundedPosition) > 0.0001) {
            splitPosition = boundedPosition
        }
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: preferredWidth > 0 ? preferredWidth : 300
    implicitHeight: preferredHeight > 0 ? preferredHeight : 200
    width: implicitWidth
    height: implicitHeight
    onSplitPositionChanged: _clampSplitPosition()
    onWidthChanged: _clampSplitPosition()
    onHeightChanged: _clampSplitPosition()
    onOrientationChanged: _clampSplitPosition()
    onHandleWidthChanged: _clampSplitPosition()
    onFirstMinimumSizeChanged: _clampSplitPosition()
    onSecondMinimumSizeChanged: _clampSplitPosition()
    Component.onCompleted: _clampSplitPosition()

    // First pane 第一面板
    Item {
        id: firstPane
        objectName: "firstPane"
        anchors.left: parent.left
        anchors.top: parent.top
        width: control.isHorizontal ? control._firstExtent : parent.width
        height: control.isHorizontal ? parent.height : control._firstExtent
        clip: true
    }
    
    // Separator handle 分隔条
    Rectangle {
        id: handle
        x: control.isHorizontal ? firstPane.width : 0
        y: control.isHorizontal ? 0 : firstPane.height
        width: control.isHorizontal ? control._safeHandleWidth : parent.width
        height: control.isHorizontal ? parent.height : control._safeHandleWidth

        // Default transparent, tint only on hover/press 默认透明，悬停/按下才着色
        color: control._splitHandleColor
        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }

        // Grip pill — draggable cue 药丸抓手，提示可拖拽
        Rectangle {
            id: grip

            readonly property int gripThickness: Enums.border.thick
            readonly property int gripLength: (handleArea.containsMouse || handleArea.pressed) ? 36 : 24

            anchors.centerIn: parent
            radius: Enums.radius.pill

            // Lengthens slightly on interaction 交互时略微变长 (px)
            width: control.isHorizontal ? gripThickness : gripLength
            height: control.isHorizontal ? gripLength : gripThickness
            Behavior on width { NumberAnimation { duration: Enums.duration.fast } }
            Behavior on height { NumberAnimation { duration: Enums.duration.fast } }

            // Neutral grey, deepens on interaction 中性灰，交互时加深
            color: control._splitGripColor
            Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
        }
        
        // Mouse area inside handle 鼠标区域放在handle内部
        MouseArea {
            id: handleArea

            property real startPos
            property real startSplit

            anchors.fill: parent
            hoverEnabled: true
            cursorShape: control.isHorizontal ? Qt.SplitHCursor : Qt.SplitVCursor
            
            onPressed: (mouse) => {
                startPos = control.isHorizontal ? mapToItem(control, mouse.x, 0).x : mapToItem(control, 0, mouse.y).y
                startSplit = control.splitPosition
            }
            
            onPositionChanged: (mouse) => {
                if (!pressed) return
                
                var currentPos = control.isHorizontal ? mapToItem(control, mouse.x, 0).x : mapToItem(control, 0, mouse.y).y
                var delta = currentPos - startPos
                if (control._availableSize <= 0) return

                var newSplit = startSplit + delta / control._availableSize
                control.splitPosition = control._boundedSplitPosition(newSplit)
            }
        }
    }
    
    // Second pane 第二面板
    Item {
        id: secondPane
        objectName: "secondPane"
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: control.isHorizontal ? control._secondExtent : parent.width
        height: control.isHorizontal ? parent.height : control._secondExtent
        clip: true
    }
}
