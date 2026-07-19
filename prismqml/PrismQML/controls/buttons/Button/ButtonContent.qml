// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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
    required property int fontSize
    required property bool pressed  // For animation timing 用于动画时长控制

    // ==================== Public Props 公开属性 ====================
    // Optional font flags 可选字体修饰
    property bool fontBold: false
    property bool fontItalic: false
    property bool fontUnderline: false
    property bool fontStrikeout: false
    // Countdown props 倒计时属性
    property bool countdownActive: false
    property int countdownRemaining: 0
    property string countdownText: "s"

    // ==================== Readonly State 只读状态 ====================
    readonly property bool hasIcon: icon !== "" ||
                                    loading ||
                                    feature === Enums.button.feature_progress_ring ||
                                    feature === Enums.button.feature_indeterminate_ring
    readonly property bool _useForegroundColor: style === Enums.button.style_primary ||
                                                style === Enums.button.style_filled ||
                                                style === Enums.button.style_gradient
    readonly property color _ringColor: _useForegroundColor ? Enums.accentForeground : Enums.accentColor
    readonly property color _ringBorderColor: _useForegroundColor ? Enums.stateColor.onAccentOverlay : Enums.stateColor.loadingBorder

    // ==================== Size 尺寸 ====================
    spacing: hasIcon ? 6 : 0

    // ==================== Content 内容 ====================
    // Loading ring 加载环
    Loader {
        id: loadingRingLoader
        width: active ? content.iconSize : 0
        height: active ? content.iconSize : 0
        active: content.loading
        anchors.verticalCenter: parent.verticalCenter

        sourceComponent: ProgressRing {
            anchors.fill: parent
            strokeWidth: Enums.border.normal
            color: content.textColor
            indeterminate: true
        }
    }

    // Progress ring 进度环
    Loader {
        id: progressRingLoader
        width: active ? content.iconSize : 0
        height: active ? content.iconSize : 0
        active: feature === Enums.button.feature_progress_ring
        anchors.verticalCenter: parent.verticalCenter

        sourceComponent: ProgressRing {
            anchors.fill: parent
            from: 0
            to: 1
            value: content.progress
            strokeWidth: Enums.border.normal
            color: content._ringColor
            trackColorLight: content._ringBorderColor
            trackColorDark: content._ringBorderColor
        }
    }

    // Indeterminate ring 不确定环
    Loader {
        id: indeterminateRingLoader
        width: active ? content.iconSize : 0
        height: active ? content.iconSize : 0
        active: feature === Enums.button.feature_indeterminate_ring
        anchors.verticalCenter: parent.verticalCenter

        sourceComponent: ProgressRing {
            anchors.fill: parent
            strokeWidth: Enums.border.normal
            indeterminate: true
            color: content._ringColor
        }
    }

    // Icon 图标
    Loader {
        id: iconLoader
        width: active ? content.iconSize : 0
        height: active ? content.iconSize : 0
        active: !content.loading && content.icon !== ""
        anchors.verticalCenter: parent.verticalCenter

        sourceComponent: Icon {
            anchors.centerIn: parent
            icon: content.icon
            iconSize: content.iconSize
            color: content.textColor
        }
    }

    // Text 文字
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
        // Bind textColor directly without a Behavior animation. 直接绑定 textColor，不添加 Behavior 动画。
        // A toggle button changes its background immediately when checked. toggle 类按钮从 unchecked 切换到 checked 时背景色会突变。
        // A 300 ms ColorAnimation passes through gray and nearly disappears on a light background. 300ms 的 ColorAnimation 会经过灰色中间态，在浅色背景上几乎不可见，表现为“切换后文字消失”。
        color: content.textColor
        visible: text !== ""
        anchors.verticalCenter: parent.verticalCenter
    }
}
