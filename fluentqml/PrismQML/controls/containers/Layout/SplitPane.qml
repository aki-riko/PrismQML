// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// SplitPane - Pure QtQuick implementation 分割器纯QtQuick实现
// Resizable two-panel split 可拖拽调整大小的两面板
Item {
    id: control
    
    // ==================== Size Priority System 尺寸优先级系统 ====================
    // Compatible with Widget.qml size system 与Widget.qml尺寸系统兼容
    property real preferredWidth: 0
    property real preferredHeight: 0
    
    implicitWidth: preferredWidth > 0 ? preferredWidth : 300
    implicitHeight: preferredHeight > 0 ? preferredHeight : 200
    width: implicitWidth
    height: implicitHeight

    // Public props 公开属性
    property int orientation: Qt.Horizontal  // Qt.Horizontal or Qt.Vertical
    property real splitPosition: 0.5  // 0-1 range
    property int handleWidth: Enums.comboBoxMetrics.scrollBarWidth
    property int minimumSize: 50
    
    // Content areas 内容区域
    property alias firstContent: firstPane.data
    property alias secondContent: secondPane.data
    
    // Internal state 内部状态
    readonly property bool isHorizontal: orientation === Qt.Horizontal

    // ==================== Public Methods 公共方法 ====================
    // Get child count 获取子组件数量
    function count() { return 2 }

    // First pane 第一面板
    Item {
        id: firstPane
        objectName: "firstPane"
        anchors.left: parent.left
        anchors.top: parent.top
        width: control.isHorizontal ? (parent.width - control.handleWidth) * control.splitPosition : parent.width
        height: control.isHorizontal ? parent.height : (parent.height - control.handleWidth) * control.splitPosition
        clip: true
    }
    
    // Separator handle 分隔条
    Rectangle {
        id: handle
        x: control.isHorizontal ? firstPane.width : 0
        y: control.isHorizontal ? 0 : firstPane.height
        width: control.isHorizontal ? control.handleWidth : parent.width
        height: control.isHorizontal ? parent.height : control.handleWidth

        // Default transparent, tint only on hover/press 默认透明，悬停/按下才着色
        color: handleArea.pressed
            ? Enums.stateColor.controlBgPressed
            : (handleArea.containsMouse ? Enums.stateColor.controlBgHover
                                        : Enums.stateColor.controlBgTransparent)
        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }

        // Grip pill — draggable cue 药丸抓手，提示可拖拽
        Rectangle {
            id: grip
            anchors.centerIn: parent
            radius: Enums.radius.pill

            // Lengthens slightly on interaction 交互时略微变长 (px)
            readonly property int gripThickness: Enums.border.thick
            readonly property int gripLength: (handleArea.containsMouse || handleArea.pressed) ? 36 : 24
            width: control.isHorizontal ? gripThickness : gripLength
            height: control.isHorizontal ? gripLength : gripThickness
            Behavior on width { NumberAnimation { duration: Enums.duration.fast } }
            Behavior on height { NumberAnimation { duration: Enums.duration.fast } }

            // Neutral grey, deepens on interaction 中性灰，交互时加深
            color: handleArea.pressed
                ? Enums.stateColor.indicatorActive
                : (handleArea.containsMouse ? Enums.stateColor.indicatorHover
                                            : Enums.stateColor.indicator)
            Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
        }
        
        // Mouse area inside handle 鼠标区域放在handle内部
        MouseArea {
            id: handleArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: control.isHorizontal ? Qt.SplitHCursor : Qt.SplitVCursor
            
            property real startPos
            property real startSplit
            
            onPressed: (mouse) => {
                startPos = control.isHorizontal ? mapToItem(control, mouse.x, 0).x : mapToItem(control, 0, mouse.y).y
                startSplit = control.splitPosition
            }
            
            onPositionChanged: (mouse) => {
                if (!pressed) return
                
                var currentPos = control.isHorizontal ? mapToItem(control, mouse.x, 0).x : mapToItem(control, 0, mouse.y).y
                var delta = currentPos - startPos
                var totalSize = control.isHorizontal 
                    ? control.width - control.handleWidth 
                    : control.height - control.handleWidth
                
                var newSplit = startSplit + delta / totalSize
                
                // Limit minimum size 限制最小尺寸
                var minRatio = control.minimumSize / totalSize
                newSplit = Math.max(minRatio, Math.min(1 - minRatio, newSplit))
                
                control.splitPosition = newSplit
            }
        }
    }
    
    // Second pane 第二面板
    Item {
        id: secondPane
        objectName: "secondPane"
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: control.isHorizontal ? parent.width - firstPane.width - control.handleWidth : parent.width
        height: control.isHorizontal ? parent.height : parent.height - firstPane.height - control.handleWidth
        clip: true
    }
}
