// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../../.."
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// PopupSmoothScroll: Smooth scroll for popup/dropdown scenarios. Must be placed INSIDE the Flickable/ListView as a child. 弹窗平滑滚动。必须作为 Flickable/ListView 的子元素放置。
// Usage 用法:
//   ListView {
//       id: listView
//       interactive: false
//       PopupSmoothScroll { flickable: listView }
//   }
Item {
    id: control
    
    // ==================== Required Props 必需属性 ====================
    required property Flickable flickable  // Parent flickable/listview 父级Flickable
    
    // ==================== Config Props 配置属性 ====================
    property int duration: Enums.duration.scroll
    property real step: Enums.spacing.xxxl * 2  // Smaller step for popup 弹窗较小步长
    property int easing: Easing.OutCubic
    
    // ==================== Internal State 内部状态 ====================
    property real _targetY: 0
    property real _smoothY: flickable ? flickable.contentY : 0
    
    // Fill parent to receive wheel events 填充父级以接收滚轮事件
    anchors.fill: parent
    
    // Sync contentY with animated value 同步contentY与动画值
    on_SmoothYChanged: if (flickable) flickable.contentY = _smoothY
    
    Behavior on _smoothY {
        enabled: control.enabled && control.flickable && control.flickable.contentHeight > control.flickable.height
        NumberAnimation { duration: control.duration; easing.type: control.easing }
    }
    
    // ==================== Public Methods 公开方法 ====================
    function scrollTo(targetY) {
        if (!flickable) return
        var maxY = Math.max(0, flickable.contentHeight - flickable.height)
        _targetY = Math.max(0, Math.min(maxY, targetY))
        _smoothY = _targetY
    }
    
    function scrollBy(delta) {
        if (!flickable) return
        var maxY = Math.max(0, flickable.contentHeight - flickable.height)
        _targetY = Math.max(0, Math.min(maxY, _targetY + delta))
        _smoothY = _targetY
    }
    
    // ==================== Wheel Handler 滚轮处理 ====================
    // WheelHandler receives events in parent's area WheelHandler在父级区域接收事件
    WheelHandler {
        onWheel: (event) => {
            if (!control.enabled || !control.flickable) {
                event.accepted = false
                return
            }
            
            // Check if scrollable 检查是否可滚动
            if (control.flickable.contentHeight <= control.flickable.height) {
                event.accepted = false
                return
            }
            
            var delta = -event.angleDelta.y / 120 * control.step
            control.scrollBy(delta)
            event.accepted = true
        }
    }
    
    // Sync initial position 同步初始位置
    Component.onCompleted: {
        if (flickable) {
            _targetY = flickable.contentY
            _smoothY = flickable.contentY
        }
    }
}
