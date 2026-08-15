// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ConstantsThemeColors - Fluent base color tokens Fluent 基础颜色 token
QtObject {
    id: themeColors

    // ==================== Content 内容 ====================
    // Backgrounds 背景
    // compact-nav window: outer=navigation+titlebar, inner=content area
    readonly property color backgroundDark: "#202020"   // Outer dark 外层深色
    readonly property color backgroundLight: "#f0f4f9"  // Outer light 外层浅色
    readonly property color surfaceDark: "#272727"      // Inner dark 内层深色
    readonly property color surfaceLight: "#f7f9fc"     // Inner light 内层浅色
    readonly property color cardDark: "#2d2d2d"  // Card uses opaque background 卡片使用不透明背景
    readonly property color cardLight: "#ffffff"  // Card uses opaque background 卡片使用不透明背景
    readonly property color toastCardDark: "#2d2d2d"  // Toast needs opaque background Toast需要不透明背景
    readonly property color toastCardLight: "#ffffff"  // Toast needs opaque background Toast需要不透明背景
    readonly property color dialogDark: "#2d2d30"
    readonly property color dialogLight: "#ffffff"
    readonly property color headerDark: "#252525"
    readonly property color headerLight: "#fafafa"
    readonly property color tableHoverDark: Qt.rgba(1, 1, 1, 0.06)
    // 全局统一: table/list hover 跟 controlBgHover 一致 (#f0f0f0)
    readonly property color tableHoverLight: "#f0f0f0"
    readonly property color alternateRowDark: Qt.rgba(1, 1, 1, 0.02)
    // 奇数行底色 — 比 cardLight 略灰但比 hover 淡, 让 hover 仍能跟它区分
    readonly property color alternateRowLight: "#f8f8f8"
    readonly property color scrollTrackDark: Qt.rgba(1, 1, 1, 0.04)
    readonly property color scrollTrackLight: "#f0f0f0"
    readonly property color scrollHandleDark: Qt.rgba(1, 1, 1, 0.2)
    readonly property color scrollHandleLight: "#bbb"
    readonly property color scrollHandleHoverDark: Qt.rgba(1, 1, 1, 0.3)
    readonly property color scrollHandleHoverLight: "#999"
    readonly property color tableBgDark: "#1a1a1a"
    readonly property color tableBgLight: "#f3f3f3"

    // Foregrounds 前景
    readonly property color foregroundDark: "#ffffff"
    readonly property color foregroundLight: "#1a1a1a"
    readonly property color secondaryForegroundDark: "#9d9d9d"
    readonly property color secondaryForegroundLight: "#606060"
    readonly property color tertiaryForegroundDark: "#717171"
    readonly property color tertiaryForegroundLight: "#8a8a8a"
    readonly property color disabledForegroundDark: "#6d6d6d"
    readonly property color disabledForegroundLight: "#a0a0a0"
    readonly property color accentForeground: "#ffffff"

    // Borders 边框
    readonly property color borderDark: "#454545"
    readonly property color borderLight: "#e5e5e5"
    readonly property color borderLightDark: "#3a3a3a"
    readonly property color borderLightLight: "#f0f0f0"
    readonly property color borderStrongDark: "#606060"
    readonly property color borderStrongLight: "#c0c0c0"
    readonly property color dividerDark: "#3d3d3d"
    readonly property color dividerLight: "#ebebeb"

    // Interaction 交互
    readonly property color hoverDark: "#3d3d3d"
    readonly property color hoverLight: "#f0f0f0"
    readonly property color pressedDark: "#333333"
    readonly property color pressedLight: "#e8e8e8"
    readonly property color disabledDark: "#4d4d4d"
    readonly property color disabledLight: "#cccccc"
    readonly property color selectedDark: "#0d3d6d"
    readonly property color selectedLight: "#cce4f7"
    readonly property color star: "#ffdc06"
    readonly property color infoAccentDark: "#60cdff"
    readonly property color infoAccentLight: "#005fb7"

    // Shadows 阴影
    readonly property color shadowDark: "#40000000"
    readonly property color shadowLight: "#20000000"
    readonly property color shadowStrongDark: "#60000000"
    readonly property color shadowStrongLight: "#30000000"

    // Tooltip/Flyout backgrounds Tooltip/弹出层背景
    readonly property color tooltipBgDark: "#282828"
    readonly property color tooltipBgLight: "#f8f8f8"

    // Tab selected background Tab选中背景
    readonly property color tabSelectedDark: "#282828"
    readonly property color tabSelectedLight: "#f9f9f9"
}
