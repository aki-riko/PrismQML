// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// StatusLevel - Status level enum and semantic colors 状态级别枚举与语义色
// For: InfoBar, Toast, FilledButton, StatusTag 适用于
QtObject {
    id: root
    
    required property bool isDark
    property bool isNeo: false
    required property color accentColor
    required property var constants
    
    // Level enums 级别枚举
    readonly property int info: 0
    readonly property int success: 1
    readonly property int warning: 2
    readonly property int error: 3
    readonly property int attention: 4
    readonly property int processing: 5
    
    // String form 字符串形式
    readonly property string infoStr: "info"
    readonly property string successStr: "success"
    readonly property string warningStr: "warning"
    readonly property string errorStr: "error"
    readonly property string attentionStr: "attention"
    readonly property string processingStr: "processing"
    
    // Semantic colors (Light theme) 语义色（浅色主题）
    readonly property color infoColor: constants.semanticColors.infoLight
    readonly property color successColor: constants.semanticColors.successLight
    readonly property color warningColor: constants.semanticColors.warningLight
    readonly property color errorColor: constants.semanticColors.errorLight
    readonly property color attentionColor: constants.semanticColors.attentionLight
    readonly property color processingColor: constants.semanticColors.processingLight
    
    // Semantic colors (Dark theme) 语义色（深色主题）
    readonly property color infoColorDark: constants.semanticColors.infoDark
    readonly property color successColorDark: constants.semanticColors.successDark
    readonly property color warningColorDark: constants.semanticColors.warningDark
    readonly property color errorColorDark: constants.semanticColors.errorDark
    readonly property color attentionColorDark: constants.semanticColors.attentionDark
    readonly property color processingColorDark: constants.semanticColors.processingDark
    
    // Get color by level 根据level获取颜色
    function getColorByLevel(level) {
        if (isNeo) {
            // neo 高饱和语义色(success/warning/error/info), attention/processing 回退橙主色
            switch (level) {
                case 1: return constants.neoColors.success
                case 2: return constants.neoColors.warning
                case 3: return constants.neoColors.danger
                case 0: return constants.neoColors.info
                default: return constants.neoColors.primary
            }
        }
        switch (level) {
            case 1: return root.isDark ? successColorDark : successColor
            case 2: return root.isDark ? warningColorDark : warningColor
            case 3: return root.isDark ? errorColorDark : errorColor
            case 4: return root.isDark ? attentionColorDark : attentionColor
            case 5: return root.isDark ? processingColorDark : processingColor
            default: return root.isDark ? infoColorDark : infoColor
        }
    }
    
    // Get color by severity string 根据severity获取颜色
    function getColor(severity) {
        switch (severity) {
            case "success": return root.isDark ? successColorDark : successColor
            case "warning": return root.isDark ? warningColorDark : warningColor
            case "error": return root.isDark ? errorColorDark : errorColor
            case "attention": return root.isDark ? attentionColorDark : attentionColor
            case "processing": return root.isDark ? processingColorDark : processingColor
            default: return root.isDark ? infoColorDark : infoColor
        }
    }
    
    // Background color 背景色
    function getBgColor(severity) {
        if (root.isDark) {
            var c = getColor(severity)
            return Qt.rgba(c.r * 0.25, c.g * 0.25, c.b * 0.25, 1)
        } else {
            switch (severity) {
                case "success": return constants.semanticColors.successBgLight
                case "warning": return constants.semanticColors.warningBgLight
                case "error": return constants.semanticColors.errorBgLight
                case "attention": return constants.semanticColors.attentionBgLight
                case "processing": return constants.semanticColors.processingBgLight
                default: return constants.semanticColors.infoBgLight
            }
        }
    }
}
