// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../containers"

// ProgressCore - Progress base class 进度基类
Widget {
    id: control
    
    property real value: 0
    property real from: 0
    property real to: 100
    // Qt-style range aliases Qt风格范围别名
    property alias minimum: control.from
    property alias maximum: control.to
    property bool indeterminate: false
    property bool paused: false
    property bool error: false  // Error state 错误状态

    // Custom color props (per-theme) 颜色自定义属性（分主题）
    property color fillColorLight: Enums.accentColor
    property color fillColorDark: Enums.accentColor
    property color trackColorLight: Enums.stateColor.track
    property color trackColorDark: Enums.stateColor.whiteOverlay
    readonly property real position: (value - from) / (to - from)
    property color progressColor: {
        if (error) return Enums.isDark ? Enums.statusLevel.errorColorDark : Enums.statusLevel.errorColor
        if (paused) return Enums.isDark ? Enums.statusLevel.warningColorDark : Enums.statusLevel.warningColor
        return Enums.isDark ? fillColorDark : fillColorLight
    }
    readonly property color trackColor: Enums.isDark ? trackColorDark : trackColorLight
    
    // ==================== Qt-Style Convenience Methods Qt风格便捷方法 ====================
    
    
    function setRange(min, max) {
        from = min
        to = max
    }

    /// 重置进度到初始状态: value=from, 清掉 indeterminate/paused/error
    /// 任务可重用同一个 ProgressBar 实例时调用
    function reset() {
        value = from
        indeterminate = false
        paused = false
        error = false
    }

    function pause() {
        paused = true
    }
    
    function resume() {
        paused = false
    }
    
    
    function isPaused() {
        return paused
    }
    
    
    function isError() {
        return error
    }
    
    // Color setter methods 颜色设置方法
    function setFillColor(light, dark) {
        fillColorLight = light
        fillColorDark = dark
    }

    function setTrackColor(light, dark) {
        trackColorLight = light
        trackColorDark = dark
    }
    
    
    // Check if indeterminate 检查是否不确定
    function isIndeterminate() {
        return indeterminate
    }
    
    
    // Get current value 获取当前值
    function getValue() {
        return value
    }
    
    // Get position (0-1) 获取位置
    function getPosition() {
        return position
    }
}
