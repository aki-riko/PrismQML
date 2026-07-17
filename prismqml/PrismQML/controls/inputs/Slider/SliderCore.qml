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

    // ==================== Public Props 公开属性 ====================
    property int type: Enums.slider.type_default
    property real value: 50
    property real from: 0
    property real to: 100
    property real stepSize: 1
    property int orientation: Qt.Horizontal
    // snapMode: 0=NoSnap (free drag) 自由拖动
    //          1=SnapOnRelease (snap after release) 松手后吸附
    //          2=SnapAlways (default, snap while dragging) 默认实时吸附
    // Match the Qt Slider enum behavior 与 Qt Slider 同名枚举行为一致
    property int snapMode: 2
    property color handleColor: Enums.isPrismDesign ? Enums.stateColor.controlBg : Enums.gray.handle  // Custom handle color 自定义手柄颜色
    property string suffix: ""
    property int decimals: 0
    // Optional tooltip formatter: (value)->string 可选的 tooltip 格式化函数
    // Overrides value.toFixed(decimals)+suffix when non-null 非 null 时覆盖默认格式
    // Supports timeline values such as 00:33 支持时间轴等自定义文本
    property var displayValueFn: null
    property real firstValue: 25
    property real secondValue: 75
    property color accentColor: Enums.accentColor

    // ==================== Internal Props 内部属性 ====================
    property real _targetValue: value
    // Disable smooth animation while dragging to avoid feedback loops 拖动时禁用平滑动画以避免反馈振荡
    // The old drag.target implementation broke handle.x bindings 旧 drag.target 实现会破坏 handle.x 绑定
    property bool _dragging: false

    // ==================== Readonly State 只读状态 ====================
    readonly property color _trackColor: control.enabled ? Enums.stateColor.sliderTrack : Enums.stateColor.sliderTrackDisabled
    readonly property color _progressColor: control.enabled ? control.accentColor : Enums.stateColor.disabledBorder
    readonly property int _handleBorderWidth: Enums.isNeobrutalism ? Enums.neo.borderWidth
                                                                  : (Enums.isPrismDesign ? Enums.prismDesign.borderWidth : Enums.border.thin)
    readonly property color _handleBorderColor: control.enabled
                                                ? (Enums.isPrismDesign ? Enums.stateColor.borderStrong : Enums.stateColor.border)
                                                : Enums.stateColor.disabledBorder
    readonly property color _handleInnerColor: control.enabled ? control.accentColor : Enums.textColor.disabled
    readonly property bool isHorizontal: orientation === Qt.Horizontal
    readonly property bool _isDefault: type === Enums.slider.type_default
    readonly property bool _isRange: type === Enums.slider.type_range

    // ==================== Signals 信号 ====================
    signal valueModified(real newValue)
    signal sliderMoved(real first, real second)  // Range type Range类型

    // ==================== Internal Methods 内部方法 ====================
    // Apply snapMode for dragging and release 根据拖动或松手阶段应用 snapMode
    function _maybeSnap(v, dragging) {
        if (stepSize <= 0) return v
        if (snapMode === 0) return v
        if (snapMode === 1 && dragging) return v
        return Math.round(v / stepSize) * stepSize
    }

    // Format tooltip text for default/range implementations 格式化默认及范围滑块的提示文本
    function _tipText(v) {
        return displayValueFn ? displayValueFn(v) : (v.toFixed(decimals) + suffix)
    }

    // ==================== Public Methods 公开方法 ====================
    // Set range 设置范围
    function setRange(minimum, maximum) {
        from = minimum
        to = maximum
        value = Math.max(from, Math.min(to, value))
    }

    function smoothSetValue(newValue) {
        var clampedValue = Math.max(from, Math.min(to, newValue))
        _targetValue = clampedValue
        value = _targetValue
        valueModified(clampedValue)
    }

    // Set value 设置值
    function setValue(v) { value = Math.max(from, Math.min(to, v)) }
    function getValue() { return value }

    function minimum() { return from }

    function maximum() { return to }

    function isEnabled() { return enabled }

    // ==================== Size 尺寸 ====================
    implicitWidth: isHorizontal ? 200 : Enums.spacing.xxxl
    implicitHeight: isHorizontal ? Enums.spacing.xxxl : 200

    // ==================== Content 内容 ====================
    Behavior on value {
        enabled: !control._dragging
        NumberAnimation {
            duration: Enums.duration.fast
            easing.type: Easing.OutCubic
        }
    }

    // Default slider implementation with tooltip 默认带提示的滑块实现
    Loader {
        anchors.fill: parent
        active: _isDefault
        sourceComponent: defaultSliderComponent
    }
    
    Component {
        id: defaultSliderComponent
        Item {
            readonly property bool hovered: handleArea.containsMouse || trackArea.containsMouse || wheelArea.containsMouse
            readonly property bool pressed: handleArea.pressed

            anchors.fill: parent

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
                color: control._trackColor
                
                // Progress 进度
                Rectangle {
                    width: isHorizontal ? handle.x + handle.width / 2 : parent.width
                    height: isHorizontal ? parent.height : parent.height - handle.y - handle.height / 2
                    y: isHorizontal ? 0 : handle.y + handle.height / 2
                    radius: parent.radius
                    color: control._progressColor
                }
                
                MouseArea {
                    id: trackArea
                    anchors.fill: parent
                    anchors.margins: -Enums.spacing.m
                    enabled: control.enabled
                    hoverEnabled: true
                    onClicked: (mouse) => {
                        var trackPoint = trackArea.mapToItem(track, mouse.x, mouse.y)
                        var pos = isHorizontal ? trackPoint.x / track.width : 1 - trackPoint.y / track.height
                        pos = Math.max(0, Math.min(1, pos))
                        var newValue = control.from + pos * (control.to - control.from)
                        newValue = Math.round(newValue / control.stepSize) * control.stepSize
                        newValue = Math.max(control.from, Math.min(control.to, newValue))
                        control.value = newValue
                        control.valueModified(newValue)
                    }
                }
            }
            
            // Handle 手柄
            Rectangle {
                id: handle
                // Clamp ratio during transient range changes 在量程瞬时变化时将比例钳制到 [0,1]
                // Prevent the handle from escaping before to/from settle 防止程序改值早于量程更新时手柄越界
                readonly property real _ratio: (control.to - control.from) !== 0
                    ? Math.max(0, Math.min(1, (control.value - control.from) / (control.to - control.from)))
                    : 0

                width: Enums.controlSize.switchHeight; height: Enums.controlSize.switchHeight; radius: width / 2
                x: isHorizontal ? _ratio * (track.width - width) + track.x : (parent.width - width) / 2
                y: isHorizontal ? (parent.height - height) / 2 : (1 - _ratio) * (track.height - height) + track.y
                color: control.handleColor
                border.width: control._handleBorderWidth
                border.color: control._handleBorderColor
                
                Rectangle {
                    anchors.centerIn: parent
                    // Handle inner circle: shrinks on press, grows on hover 内圆:按下缩小,悬停放大
                    width: handleArea.pressed ? Enums.iconSize.micro : (hovered ? Enums.iconSize.xs : Enums.iconSize.tiny)
                    height: width; radius: width / 2
                    color: control._handleInnerColor
                    Behavior on width { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
                }
                
                // ToolTip (default shows on hover/press) 默认悬浮/按下时显示
                TooltipCore {
                    x: (parent.width - width) / 2
                    y: -height - Enums.spacing.m
                    text: control._tipText(control.value)
                    visible: hovered || pressed
                    // Reposition with handle.x during drag or programmatic changes 拖动或程序改值时跟随手柄重定位
                    followAnchor: hovered || pressed
                }

                // Avoid drag.target because it breaks the handle.x binding 避免使用会破坏 handle.x 绑定的 drag.target
                // Map the pointer to value while handle.x stays bound to value 按指针位置映射 value 并保持 handle.x 绑定
                // This keeps programmatic updates and user dragging stable 保证程序更新与用户拖动稳定
                MouseArea {
                    id: handleArea

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
                            control.valueModified(newValue)
                        }
                    }

                    anchors.fill: parent
                    anchors.margins: -Enums.spacing.xs
                    enabled: control.enabled
                    hoverEnabled: true
                    preventStealing: true

                    onPressed: control._dragging = true
                    onReleased: {
                        control._dragging = false
                        // Snap after release for SnapOnRelease/SnapAlways 松手后执行吸附
                        var snapped = control._maybeSnap(control.value, false)
                        snapped = Math.max(control.from, Math.min(control.to, snapped))
                        if (snapped !== control.value) {
                            control.value = snapped
                            control.valueModified(snapped)
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
    
    // Range slider implementation 范围滑块实现
    Loader {
        anchors.fill: parent
        active: _isRange
        sourceComponent: rangeSliderComponent
    }
    
    Component {
        id: rangeSliderComponent
        Item {
            readonly property real firstPos: (control.firstValue - control.from) / (control.to - control.from)
            readonly property real secondPos: (control.secondValue - control.from) / (control.to - control.from)

            anchors.fill: parent

            Rectangle {
                id: groove
                anchors.centerIn: parent
                width: isHorizontal ? parent.width : Enums.radius.small
                height: isHorizontal ? Enums.radius.small : parent.height
                radius: Enums.radius.tiny
                color: control._trackColor
            }
            
            Rectangle {
                x: isHorizontal ? groove.x + groove.width * Math.min(firstPos, secondPos) : groove.x
                y: isHorizontal ? groove.y : groove.y + groove.height * (1 - Math.max(firstPos, secondPos))
                width: isHorizontal ? groove.width * Math.abs(secondPos - firstPos) : Enums.radius.small
                height: isHorizontal ? Enums.radius.small : groove.height * Math.abs(secondPos - firstPos)
                radius: Enums.radius.tiny
                color: control._progressColor
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
                border.width: control._handleBorderWidth
                border.color: control._handleBorderColor
                
                Rectangle {
                    anchors.centerIn: parent
                    // Handle inner circle: shrinks on press, grows on hover 内圆:按下缩小,悬停放大
                    width: rangeHandleArea.pressed ? Enums.iconSize.micro : (rangeHandleArea.containsMouse ? Enums.iconSize.xs : Enums.iconSize.tiny)
                    height: width; radius: width / 2
                    color: control._handleInnerColor
                    Behavior on width { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
                }
                
                TooltipCore {
                    x: (parent.width - width) / 2
                    y: -height - Enums.spacing.m
                    text: control.displayValueFn ? control.displayValueFn(handleValue)
                                                 : Math.round(handleValue).toString()
                    visible: rangeHandleArea.containsMouse || rangeHandleArea.pressed
                    followAnchor: rangeHandleArea.containsMouse || rangeHandleArea.pressed
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
