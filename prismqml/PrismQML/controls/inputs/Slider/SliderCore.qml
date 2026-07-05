// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "../../feedback"

// Slider - Unified slider component 统一滑块组件
// Distinguish by type: type_default/type_range 通过type区分
Item {
    id: control
    
    // ==================== Type 类型 ====================
    property int type: Enums.slider.type_default
    
    // ==================== Common Props 通用属性 ====================
    property real value: 50
    property real from: 0
    property real to: 100
    property real stepSize: 1
    property int orientation: Qt.Horizontal
    // snapMode: 0=NoSnap (自由拖,可停在任意位置)
    //          1=SnapOnRelease (拖动时自由,松手吸附到 step)
    //          2=SnapAlways (默认,实时吸附到 step,与 stepSize 配合用)
    // 兼容 Qt Slider 同名 enum 行为
    property int snapMode: 2

    // 内部辅助:按 snapMode 决定是否吸附 (松手时永远吸附,拖动时看 mode)
    function _maybeSnap(v, dragging) {
        if (stepSize <= 0) return v
        if (snapMode === 0) return v
        if (snapMode === 1 && dragging) return v
        return Math.round(v / stepSize) * stepSize
    }
    
    // ==================== ToolTip Props ToolTip属性 ====================
    property string suffix: ""
    property int decimals: 0
    
    // ==================== Range Type Props Range类型属性 ====================
    property real firstValue: 25
    property real secondValue: 75
    
    // ==================== Signals 信号 ====================
    signal valueModified(real newValue)
    signal sliderMoved(real first, real second)  // Range type Range类型
    
    // ==================== Theme 主题 ====================
    property color accentColor: Enums.accentColor
    property color handleColor: Enums.gray.handle  // Custom handle color 自定义手柄颜色
    readonly property bool isHorizontal: orientation === Qt.Horizontal

    // Set range 设置范围
    function setRange(minimum, maximum) {
        from = minimum
        to = maximum
        value = Math.max(from, Math.min(to, value))
    }
    
    // ==================== Size 尺寸 ====================
    implicitWidth: isHorizontal ? 200 : Enums.spacing.xxxl
    implicitHeight: isHorizontal ? Enums.spacing.xxxl : 200
    
    // ==================== Internal State 内部状态 ====================
    readonly property bool _isDefault: type === Enums.slider.type_default
    readonly property bool _isRange: type === Enums.slider.type_range
    
    // ==================== Smooth Value Animation 平滑值动画 ====================
    property real _targetValue: value
    // 拖动中标记:拖动时禁用平滑动画,避免动画回写 value 与拖动形成反馈振荡
    // (旧实现 drag.target 破坏 handle.x 绑定 + Behavior 回写 → 手柄乱飞)
    property bool _dragging: false

    Behavior on value {
        enabled: !control._dragging
        NumberAnimation {
            duration: Enums.duration.fast
            easing.type: Easing.OutCubic
        }
    }
    
    function smoothSetValue(newValue) {
        _targetValue = Math.max(from, Math.min(to, newValue))
        value = _targetValue
        valueModified(value)
    }

    // ==================== Public Methods 公共方法 ====================
    // Set value 设置值
    function setValue(v) { value = Math.max(from, Math.min(to, v)) }
    function getValue() { return value }

    function minimum() { return from }

    function maximum() { return to }

    function isEnabled() { return enabled }

    // ==================== Default Slider Impl 默认滑块(带tooltip) ====================
    Loader {
        anchors.fill: parent
        active: _isDefault
        sourceComponent: defaultSliderComponent
    }
    
    Component {
        id: defaultSliderComponent
        Item {
            anchors.fill: parent
            
            readonly property bool hovered: handleArea.containsMouse || trackArea.containsMouse || wheelArea.containsMouse
            readonly property bool pressed: handleArea.pressed
            
            // Mouse wheel support 鼠标滚轮支持
            MouseArea {
                id: wheelArea
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
                hoverEnabled: true
                
                onWheel: (event) => {
                    if (!control.enabled) return
                    var delta = event.angleDelta.y / 120 * control.stepSize
                    control.smoothSetValue(control.value + delta)
                    event.accepted = true
                }
            }
            
            // Track 轨道
            Rectangle {
                id: track
                anchors.centerIn: parent
                width: isHorizontal ? parent.width : Enums.radius.small
                height: isHorizontal ? Enums.radius.small : parent.height
                radius: Enums.radius.tiny
                color: Enums.stateColor.border
                
                // Progress 进度
                Rectangle {
                    width: isHorizontal ? handle.x + handle.width / 2 : parent.width
                    height: isHorizontal ? parent.height : parent.height - handle.y - handle.height / 2
                    y: isHorizontal ? 0 : handle.y + handle.height / 2
                    radius: parent.radius
                    color: control.enabled ? accentColor : Enums.stateColor.disabledGray
                }
                
                MouseArea {
                    id: trackArea
                    anchors.fill: parent
                    anchors.margins: -Enums.spacing.m
                    enabled: control.enabled
                    hoverEnabled: true
                    onClicked: (mouse) => {
                        var pos = isHorizontal ? mouse.x / parent.width : 1 - mouse.y / parent.height
                        var newValue = control.from + pos * (control.to - control.from)
                        newValue = Math.round(newValue / control.stepSize) * control.stepSize
                        control.value = Math.max(control.from, Math.min(control.to, newValue))
                        control.valueModified(control.value)
                    }
                }
            }
            
            // Handle 手柄
            Rectangle {
                id: handle
                width: Enums.controlSize.switchHeight; height: Enums.controlSize.switchHeight; radius: width / 2
                x: isHorizontal ? (control.value - control.from) / (control.to - control.from) * (track.width - width) + track.x : (parent.width - width) / 2
                y: isHorizontal ? (parent.height - height) / 2 : (1 - (control.value - control.from) / (control.to - control.from)) * (track.height - height) + track.y
                color: control.handleColor
                border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin  // neo 粗黑边
                border.color: Enums.stateColor.border
                
                Rectangle {
                    anchors.centerIn: parent
                    // Handle inner circle: shrinks on press, grows on hover 内圆:按下缩小,悬停放大
                    width: handleArea.pressed ? Enums.iconSize.micro : (hovered ? Enums.iconSize.xs : Enums.iconSize.tiny)
                    height: width; radius: width / 2
                    color: control.enabled ? accentColor : Enums.gray.disabled
                    Behavior on width { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
                }
                
                // ToolTip (default shows on hover/press) 默认悬浮/按下时显示
                TooltipCore {
                    x: (parent.width - width) / 2
                    y: -height - Enums.spacing.m
                    text: control.value.toFixed(control.decimals) + control.suffix
                    visible: hovered || pressed
                }
                
                // 不用 drag.target(会破坏 handle.x 与 value 的绑定,导致程序改
                // value 时手柄不动 + Behavior 回写振荡)。改为按鼠标落点映射到
                // value,handle.x 始终绑定 value,程序化更新与用户拖动都稳。
                MouseArea {
                    id: handleArea
                    anchors.fill: parent
                    anchors.margins: -Enums.spacing.xs
                    enabled: control.enabled
                    hoverEnabled: true
                    preventStealing: true

                    function _applyFromGlobal(gx, gy) {
                        var p = track.mapFromGlobal(gx, gy)
                        var pos = isHorizontal
                            ? p.x / track.width
                            : 1 - p.y / track.height
                        pos = Math.max(0, Math.min(1, pos))
                        var newValue = control.from + pos * (control.to - control.from)
                        newValue = control._maybeSnap(newValue, true)
                        newValue = Math.max(control.from, Math.min(control.to, newValue))
                        if (newValue !== control.value) {
                            control.value = newValue
                            control.valueModified(control.value)
                        }
                    }

                    onPressed: control._dragging = true
                    onReleased: {
                        control._dragging = false
                        // 松手吸附(SnapOnRelease/SnapAlways)
                        var snapped = control._maybeSnap(control.value, false)
                        if (snapped !== control.value) {
                            control.value = Math.max(control.from, Math.min(control.to, snapped))
                            control.valueModified(control.value)
                        }
                    }
                    onPositionChanged: (mouse) => {
                        if (pressed) {
                            var g = mapToGlobal(mouse.x, mouse.y)
                            _applyFromGlobal(g.x, g.y)
                        }
                    }
                }
            }
        }
    }
    
    // ==================== Range Slider Impl 范围滑块 ====================
    Loader {
        anchors.fill: parent
        active: _isRange
        sourceComponent: rangeSliderComponent
    }
    
    Component {
        id: rangeSliderComponent
        Item {
            anchors.fill: parent
            
            readonly property real firstPos: (control.firstValue - control.from) / (control.to - control.from)
            readonly property real secondPos: (control.secondValue - control.from) / (control.to - control.from)
            
            Rectangle {
                id: groove
                anchors.centerIn: parent
                width: isHorizontal ? parent.width : Enums.radius.small
                height: isHorizontal ? Enums.radius.small : parent.height
                radius: Enums.radius.tiny
                color: control.enabled ? (Enums.stateColor.sliderTrack) : (Enums.stateColor.sliderTrackDisabled)
            }
            
            Rectangle {
                x: isHorizontal ? groove.x + groove.width * Math.min(firstPos, secondPos) : groove.x
                y: isHorizontal ? groove.y : groove.y + groove.height * (1 - Math.max(firstPos, secondPos))
                width: isHorizontal ? groove.width * Math.abs(secondPos - firstPos) : Enums.radius.small
                height: isHorizontal ? Enums.radius.small : groove.height * Math.abs(secondPos - firstPos)
                radius: Enums.radius.tiny
                color: control.enabled ? accentColor : Enums.gray.disabled
            }
            
            RangeHandle { handleValue: control.firstValue; onValueChanged: (v) => { control.firstValue = v; control.sliderMoved(control.firstValue, control.secondValue) } }
            RangeHandle { handleValue: control.secondValue; onValueChanged: (v) => { control.secondValue = v; control.sliderMoved(control.firstValue, control.secondValue) } }
            
            component RangeHandle: Rectangle {
                property real handleValue: 0
                signal valueChanged(real v)
                
                width: Enums.controlSize.switchHeight; height: Enums.controlSize.switchHeight; radius: width / 2
                x: isHorizontal ? Math.max(0, Math.min(parent.width-width, (parent.width-width)*((handleValue-control.from)/(control.to-control.from)))) : (parent.width-width)/2
                y: isHorizontal ? (parent.height-height)/2 : Math.max(0, Math.min(parent.height-height, (parent.height-height)*(1-(handleValue-control.from)/(control.to-control.from))))
                color: control.handleColor
                border.width: Enums.border.thin; border.color: Enums.stateColor.border
                
                Rectangle {
                    anchors.centerIn: parent
                    // Handle inner circle: shrinks on press, grows on hover 内圆:按下缩小,悬停放大
                    width: rangeHandleArea.pressed ? Enums.iconSize.micro : (rangeHandleArea.containsMouse ? Enums.iconSize.xs : Enums.iconSize.tiny)
                    height: width; radius: width / 2
                    color: control.enabled ? control.accentColor : Enums.gray.disabled
                    Behavior on width { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
                }
                
                TooltipCore {
                    x: (parent.width - width) / 2
                    y: -height - Enums.spacing.m
                    text: Math.round(handleValue).toString()
                    visible: rangeHandleArea.containsMouse || rangeHandleArea.pressed
                }
                
                MouseArea {
                    id: rangeHandleArea
                    anchors.fill: parent
                    hoverEnabled: true
                    drag.target: parent
                    drag.axis: isHorizontal ? Drag.XAxis : Drag.YAxis
                    drag.minimumX: 0; drag.maximumX: parent.parent.width - parent.width
                    drag.minimumY: 0; drag.maximumY: parent.parent.height - parent.height
                    enabled: control.enabled
                    preventStealing: true
                    
                    onPositionChanged: {
                        var pos = isHorizontal ? parent.x / (parent.parent.width - parent.width) : 1 - parent.y / (parent.parent.height - parent.height)
                        pos = Math.max(0, Math.min(1, pos))
                        var newVal = control.from + pos * (control.to - control.from)
                        if (control.stepSize > 0) newVal = Math.round(newVal / control.stepSize) * control.stepSize
                        valueChanged(newVal)
                    }
                }
            }
        }
    }
}
