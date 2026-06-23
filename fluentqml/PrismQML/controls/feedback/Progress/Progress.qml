// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal"

// Progress - Unified progress component 统一进度组件
// Types 类型: Enums.progress.type_bar / type_bar_filled / type_ring
// Modes 模式: indeterminate (不确定进度), paused (暂停), error (错误)
Item {
    id: control
    
    // ==================== Type 类型 ====================
    property int type: Enums.progress.type_bar
    
    // ==================== Progress Props 进度属性 ====================
    property real value: 0
    property real from: 0
    property real to: 100
    property alias minimum: control.from
    property alias maximum: control.to
    
    // ==================== State 状态 ====================
    property bool indeterminate: false
    property bool paused: false
    property bool error: false
    property bool running: true  // For indeterminate ring 用于不确定环形
    
    // ==================== Appearance 外观 ====================
    property int strokeWidth: Enums.controlSize.progressRingStroke  // Ring stroke width 环形线宽
    property string text: ""     // Filled bar/ring text 文字
    property bool showText: true // Show text 显示文字

    // ==================== Compat Methods 兼容方法 ====================
    function setRange(min, max) { from = min; to = max }
    function pause() { paused = true }
    function resume() { paused = false }
    function isPaused() { return paused }
    function isError() { return error }
    function start() { running = true }
    function stop() { running = false }

    // ==================== Size 尺寸 ====================
    implicitWidth: type === Enums.progress.type_ring ? Enums.controlSize.progressRingSize : 200
    implicitHeight: type === Enums.progress.type_ring ? Enums.controlSize.progressRingSize : (type === Enums.progress.type_bar_filled ? 24 : 4)
    
    // ==================== Loader 动态加载子模块 ====================
    Loader {
        id: contentLoader
        anchors.fill: parent
        sourceComponent: control.type === Enums.progress.type_ring ? ringComponent : barComponent
    }
    
    // ==================== Bar Component 条形组件 ====================
    Component {
        id: barComponent
        ProgressBarImpl {
            value: control.value
            from: control.from
            to: control.to
            indeterminate: control.indeterminate
            paused: control.paused
            error: control.error
            showText: control.showText
            text: control.text
            filled: control.type === Enums.progress.type_bar_filled
        }
    }
    
    // ==================== Ring Component 环形组件 ====================
    Component {
        id: ringComponent
        ProgressRingImpl {
            value: control.value
            from: control.from
            to: control.to
            indeterminate: control.indeterminate
            running: control.running
            strokeWidth: control.strokeWidth
            showText: control.showText
            text: control.text
        }
    }
}
