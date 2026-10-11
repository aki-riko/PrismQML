// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../containers"
import "../../utils"

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
    // Accessible name for the progress surface; both bar and ring inherit it.
    // 进度表面的可访问名称；进度条与进度环共同继承。
    property string a11yName: ""

    // Custom color props (per-theme) 颜色自定义属性（分主题）
    property color fillColorLight: Enums.accentColor
    property color fillColorDark: Enums.accentColor
    property color trackColorLight: Enums.stateColor.track
    property color trackColorDark: Enums.isVintageTicket
        ? Enums.stateColor.progressTrack : Enums.stateColor.whiteOverlay
    // Keep progress finite and bounded for degenerate or inverted ranges 对退化或反向范围保持有限且有界
    readonly property real position: {
        var range = to - from
        if (!isFinite(range) || range <= 0) return 0
        var ratio = (value - from) / range
        if (!isFinite(ratio)) return 0
        return Math.max(0, Math.min(1, ratio))
    }
    property color progressColor: {
        if (error) return Enums.isDark ? Enums.statusLevel.errorColorDark : Enums.statusLevel.errorColor
        if (paused) return Enums.isDark ? Enums.statusLevel.warningColorDark : Enums.statusLevel.warningColor
        return Enums.isDark ? fillColorDark : fillColorLight
    }
    readonly property color trackColor: Enums.isDark ? trackColorDark : trackColorLight
    
    // ==================== Public Methods 公开方法 ====================
    
    
    function setRange(min, max) {
        from = min
        to = max
    }

    /// Reset progress to initial state (value=from, clear indeterminate/paused/error) 重置进度到初始状态: value=from, 清掉 indeterminate/paused/error
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

    // ==================== Content 内容 ====================
    // Progress reports a bounded value, so it presents as a progress bar; the name
    // stays optional because many progress surfaces are labelled by adjacent text.
    // 进度控件报告有界数值，故以进度条身份呈现；名称可选，因为许多进度表面由相邻文本标注。
    A11ySurface {
        target: control
        role: Enums.accessibility.role_progressbar
        name: control.a11yName
    }
}
