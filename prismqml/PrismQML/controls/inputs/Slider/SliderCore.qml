// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "_internal" as SliderInternal

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
    property color handleColor: Enums.gray.handle// Custom handle color 自定义手柄颜色
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
    readonly property real _handleBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color _handleBorderColor: control.enabled
                                                ? (Enums.stateColor.border)
                                                : Enums.stateColor.disabledBorder
    readonly property color _handleInnerColor: control.enabled ? control.accentColor : Enums.textColor.disabled
    readonly property int _trackRadius: Enums.isVintageTicket
                                         ? Enums.ticket.radius : Enums.radius.tiny
    readonly property bool isHorizontal: orientation === Qt.Horizontal
    readonly property bool _isDefault: type === Enums.slider.type_default
    readonly property bool _isRange: type === Enums.slider.type_range

    // ==================== Signals 信号 ====================
    signal valueModified(real newValue)
    signal sliderMoved(real first, real second)  // Range type Range类型

    // ==================== Internal Methods 内部方法 ====================
    // Apply snapMode for dragging and release 根据拖动或松手阶段应用 snapMode
    function _maybeSnap(v, dragging) {
        if (!isFinite(stepSize) || stepSize <= 0) return v
        if (snapMode === 0) return v
        if (snapMode === 1 && dragging) return v
        return Math.round(v / stepSize) * stepSize
    }

    // Return a finite normalized position for any range 返回始终有限的归一化位置
    function _safePosition(v) {
        var range = to - from
        if (!isFinite(range) || range <= 0) return 0
        var ratio = (v - from) / range
        if (!isFinite(ratio)) return 0
        return Math.max(0, Math.min(1, ratio))
    }

    // Normalize a handle offset even when the track has no travel distance 轨道没有可移动距离时也返回安全比例
    function _safeTrackPosition(offset, span) {
        if (!isFinite(span) || span <= 0) return 0
        var ratio = offset / span
        if (!isFinite(ratio)) return 0
        return Math.max(0, Math.min(1, ratio))
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
        SliderInternal.SliderDefaultContent {
            sliderControl: control
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
        SliderInternal.SliderRangeContent {
            sliderControl: control
        }
    }
}
