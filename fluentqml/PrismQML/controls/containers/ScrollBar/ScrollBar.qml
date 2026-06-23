// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// ScrollBar - Reusable Fluent style scrollbar 可复用Fluent风格滚动条
// Usage 用法:
//   ScrollBar { target: listView; scrollHelper: helper }
Rectangle {
    id: control
    
    // ==================== Required Props 必需属性 ====================
    property Flickable target: null  // Target view 目标视图（改为可选，避免创建时报错）
    property SmoothScrollHelper scrollHelper: null  // Optional: for sync 可选：用于同步
    
    // ==================== Config Props 配置属性 ====================
    property int orientation: Qt.Vertical  // Qt.Vertical or Qt.Horizontal 方向
    property int barWidth: Enums.controlSize.scrollBarWidth
    property int minHandleSize: 30  // Minimum handle size 最小手柄尺寸
    
    // ==================== Internal 内部 ====================
    readonly property bool _isVertical: orientation === Qt.Vertical
    readonly property real _contentSize: target ? (_isVertical ? target.contentHeight : target.contentWidth) : 0
    readonly property real _viewSize: target ? (_isVertical ? target.height : target.width) : 0
    readonly property real _contentPos: target ? (_isVertical ? target.contentY : target.contentX) : 0
    readonly property bool _needsBar: target && _contentSize > _viewSize
    
    // ==================== Size & Position 尺寸和位置 ====================
    width: _isVertical ? barWidth : undefined
    height: _isVertical ? undefined : barWidth
    radius: barWidth / 2
    color: Enums.stateColor.scrollTrack
    visible: _needsBar
    
    // ==================== Handle 手柄 ====================
    Rectangle {
        id: handle
        
        // Size 尺寸
        width: control._isVertical ? control.barWidth - Enums.spacing.xxs : Math.max(control.minHandleSize, control._viewSize / control._contentSize * control.width)
        height: control._isVertical ? Math.max(control.minHandleSize, control._viewSize / control._contentSize * control.height) : control.barWidth - Enums.spacing.xxs
        radius: (control._isVertical ? width : height) / 2
        
        // Position 位置
        property real maxPos: control._isVertical ? Math.max(0, control.height - height) : Math.max(0, control.width - width)
        property real maxContent: Math.max(0, control._contentSize - control._viewSize)
        property real ratio: maxContent > 0 ? control._contentPos / maxContent : 0
        
        x: control._isVertical ? (control.width - width) / 2 : Math.max(0, Math.min(maxPos, ratio * maxPos))
        y: control._isVertical ? Math.max(0, Math.min(maxPos, ratio * maxPos)) : (control.height - height) / 2
        
        // Color 颜色
        color: handleArea.pressed ? Enums.accentColor : (handleArea.containsMouse ? Enums.stateColor.scrollHandleHover : Enums.stateColor.scrollHandleDefault)
        
        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
        
        // ==================== Drag Interaction 拖拽交互 ====================
        MouseArea {
            id: handleArea
            anchors.fill: parent
            hoverEnabled: true
            drag.target: parent
            drag.axis: control._isVertical ? Drag.YAxis : Drag.XAxis
            drag.minimumX: 0
            drag.minimumY: 0
            drag.maximumX: control._isVertical ? 0 : handle.maxPos
            drag.maximumY: control._isVertical ? handle.maxPos : 0
            
            onPositionChanged: {
                if (!drag.active || handle.maxPos <= 0 || !control.target) return
                
                var newContentPos = control._isVertical
                    ? (handle.y / handle.maxPos) * handle.maxContent
                    : (handle.x / handle.maxPos) * handle.maxContent
                
                if (control._isVertical) {
                    control.target.contentY = newContentPos
                } else {
                    control.target.contentX = newContentPos
                }
                
                // Sync with helper if provided 如果提供了helper则同步
                if (control.scrollHelper) {
                    control.scrollHelper.syncPosition()
                }
            }
        }
    }
}
