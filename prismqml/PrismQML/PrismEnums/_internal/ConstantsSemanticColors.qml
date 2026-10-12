// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ConstantsSemanticColors - Shared semantic colors 共享语义色
// success/warning/error and backgrounds follow WinUI SystemFillColor resources.
// success/warning/error及其背景色取自微软WinUI SystemFillColor资源。
// Info/attention/processing/caution are project extensions without fixed WinUI values.
// info/attention/processing/caution是本项目扩展，在WinUI中没有固定值。
// Source: https://github.com/microsoft/microsoft-ui-xaml CommonStyles/Common_themeresources_any.xaml
// 来源：微软 WinUI CommonStyles/Common_themeresources_any.xaml。
QtObject {
    // Foreground semantic colors 语义前景色
    readonly property color infoLight: "#676767"  // custom neutral gray info color 自定义中性灰信息色
    readonly property color successLight: "#0f7b0f"  // WinUI SystemFillColorSuccess (Light) WinUI 成功浅色
    readonly property color warningLight: "#9d5d00"  // WinUI SystemFillColorCaution (Light) WinUI 警告浅色
    readonly property color errorLight: "#c42b1c"  // WinUI SystemFillColorCritical (Light) WinUI 错误浅色
    readonly property color processingLight: "#7b2cbf"  // custom vivid purple 自定义鲜紫色
    readonly property color attentionLight: "#0a93a8"  // custom cyan 自定义青色
    readonly property color cautionLight: "#b88600"  // custom gold 自定义金黄色

    readonly property color infoDark: "#a3a3a3"  // custom neutral gray info color 自定义中性灰信息色
    readonly property color successDark: "#6ccb5f"  // WinUI SystemFillColorSuccess (Dark) WinUI 成功深色
    readonly property color warningDark: "#c09000"  // custom darker yellow for readability 自定义调深黄色以提升可读性
    readonly property color errorDark: "#ff99a4"  // WinUI SystemFillColorCritical (Dark) WinUI 错误深色
    readonly property color processingDark: "#d8b4fe"  // custom vivid purple 自定义鲜紫色
    readonly property color attentionDark: "#33b5bf"  // custom cyan 自定义青色
    readonly property color cautionDark: "#e8c547"  // custom yellow 自定义黄色

    // Background semantic colors (light) 语义背景色（浅色）
    readonly property color infoBgLight: "#cce4f7"  // custom color token 自定义
    readonly property color successBgLight: "#dff6dd"  // WinUI SystemFillColorSuccessBackground (Light) WinUI 成功浅色背景
    readonly property color warningBgLight: "#fff4ce"  // WinUI SystemFillColorCautionBackground (Light) WinUI 警告浅色背景
    readonly property color errorBgLight: "#fde7e9"  // WinUI SystemFillColorCriticalBackground (Light) WinUI 错误浅色背景
    readonly property color attentionBgLight: "#f0e6fa"  // custom color token 自定义
    readonly property color processingBgLight: "#f3e8ff"  // custom purple background 自定义紫色背景
    readonly property color cautionBgLight: "#fff8d6"  // custom yellow background 自定义黄色背景
}
