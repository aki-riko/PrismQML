// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../feedback"
import "../../data"

// ButtonContent - Content area (icon + text + rings) 内容区域
// Internal module for Button Button内部模块
Row {
    id: content
    
    // ==================== Required Props 必需属性 ====================
    required property int feature
    required property int style
    required property string text
    required property string icon
    required property int iconSize
    required property bool loading
    required property string loadingText
    required property real progress
    required property color textColor
    required property bool controlEnabled
    required property string fontFamily
    required property int fontSize
    // Optional font flags 可选字体修饰
    property bool fontBold: false
    property bool fontItalic: false
    property bool fontUnderline: false
    property bool fontStrikeout: false
    required property bool pressed  // For animation timing 用于动画时长控制
    // Countdown props 倒计时属性
    property bool countdownActive: false
    property int countdownRemaining: 0
    property string countdownText: "s"
    
    // ==================== Layout 布局 ====================
    spacing: hasIcon ? 6 : 0
    
    readonly property bool hasIcon: icon !== "" || 
                                    loading ||
                                    feature === Enums.button.feature_progress_ring ||
                                    feature === Enums.button.feature_indeterminate_ring
    
    // ==================== Ring Color Helper 环颜色辅助 ====================
    readonly property bool _useForegroundColor: style === Enums.button.style_primary ||
                                                style === Enums.button.style_filled ||
                                                style === Enums.button.style_gradient
    readonly property color _ringColor: _useForegroundColor ? Enums.accentForeground : Enums.accentColor
    readonly property color _ringBorderColor: _useForegroundColor ? Enums.stateColor.onAccentOverlay : Enums.stateColor.loadingBorder
    
    // ==================== Loading Ring 加载环 ====================
    ProgressRing {
        id: loadingRing
        width: content.iconSize
        height: content.iconSize
        strokeWidth: Enums.border.normal
        color: content.textColor
        indeterminate: content.loading
        visible: content.loading
        anchors.verticalCenter: parent.verticalCenter
    }
    
    // ==================== Progress Ring 进度环 ====================
    Item {
        id: progressRing
        width: content.iconSize
        height: content.iconSize
        visible: feature === Enums.button.feature_progress_ring
        anchors.verticalCenter: parent.verticalCenter
        
        Rectangle {
            anchors.fill: parent
            radius: width / 2
            color: Enums.transparent
            border.width: Enums.border.normal
            border.color: content._ringBorderColor
        }
        
        Canvas {
            id: progressCanvas
            anchors.fill: parent
            property color ringColor: content._ringColor
            onRingColorChanged: requestPaint()
            
            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.strokeStyle = ringColor
                ctx.lineWidth = 2
                ctx.lineCap = "round"
                ctx.beginPath()
                ctx.arc(width/2, height/2, width/2 - 2, -Math.PI/2, -Math.PI/2 + content.progress * 2 * Math.PI, false)
                ctx.stroke()
            }
        }
        
        Connections {
            target: content
            function onProgressChanged() { progressCanvas.requestPaint() }
        }
    }
    
    // ==================== Indeterminate Ring 不确定环 ====================
    ProgressRing {
        id: indeterminateRing
        width: content.iconSize
        height: content.iconSize
        strokeWidth: Enums.border.normal
        indeterminate: true
        visible: feature === Enums.button.feature_indeterminate_ring
        anchors.verticalCenter: parent.verticalCenter
        color: content._ringColor
    }
    
    // ==================== Icon 图标 ====================
    Icon {
        id: iconItem
        icon: content.loading ? "" : content.icon
        iconSize: content.iconSize
        color: content.textColor
        visible: !content.loading && content.icon !== ""
        anchors.verticalCenter: parent.verticalCenter
    }
    
    // ==================== Text 文字 ====================
    Label {
        id: contentText
        type: Enums.label.type_body
        text: {
            if (content.countdownActive) {
                return content.countdownRemaining + content.countdownText
            }
            if (content.loading && content.loadingText !== "") {
                return content.loadingText
            }
            return content.text
        }
        font.pixelSize: content.fontSize
        font.bold: content.fontBold
        font.italic: content.fontItalic
        font.underline: content.fontUnderline || style === Enums.button.style_hyperlink
        font.strikeout: content.fontStrikeout
        // 直接绑定 textColor, 不加 Behavior 动画.
        // toggle 类按钮 unchecked->checked 时背景色突变, 文字色若做 ColorAnimation
        // 过渡 (300ms 中段 ≈ 灰色) 在浅色背景上几乎不可见, 表现为"切换后文字消失".
        color: content.textColor
        visible: text !== ""
        anchors.verticalCenter: parent.verticalCenter
    }
}
