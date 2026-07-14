// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Theme - Global theme properties 全局主题属性
// Part of Enums modular system PrismEnums模块化系统
QtObject {
    id: root
    
    // Reference to parent for isDark 引用父级获取isDark
    required property bool isDark
    // neo 皮肤标志: true 时语义色返回 neo 调色板(仅 light); false 走 Fluent 明暗逻辑(字节不变)
    property bool isNeo: false
    // Prism Design skin flag Prism Design皮肤标志: true uses prismDesign tokens 为true时使用prismDesign token。
    property bool isPrismDesign: false
    required property color accentColor
    required property color accentColorLight
    required property color accentColorDark
    required property var constants

    // Skin palettes 皮肤调色板快捷引用
    readonly property QtObject _neo: constants.neoColors
    readonly property QtObject _prismDesign: constants.prismDesign

    // ==================== Background Colors 背景色 ====================
    readonly property color backgroundColor: isNeo ? _neo.background : (isPrismDesign ? _prismDesign.background : (root.isDark ? constants.themeColors.backgroundDark : constants.themeColors.backgroundLight))
    readonly property color surfaceColor: isNeo ? _neo.surface : (isPrismDesign ? _prismDesign.surface : (root.isDark ? constants.themeColors.surfaceDark : constants.themeColors.surfaceLight))
    readonly property color cardColor: isNeo ? _neo.surface : (isPrismDesign ? _prismDesign.raised : (root.isDark ? constants.themeColors.cardDark : constants.themeColors.cardLight))
    readonly property color toastCardColor: isNeo ? _neo.surface : (isPrismDesign ? _prismDesign.overlay : (root.isDark ? constants.themeColors.toastCardDark : constants.themeColors.toastCardLight))
    readonly property color dialogColor: isNeo ? _neo.surface : (isPrismDesign ? _prismDesign.overlay : (root.isDark ? constants.themeColors.dialogDark : constants.themeColors.dialogLight))
    readonly property color headerColor: isNeo ? _neo.background : (isPrismDesign ? _prismDesign.header : (root.isDark ? constants.themeColors.headerDark : constants.themeColors.headerLight))
    readonly property color tableHoverColor: isNeo ? _neo.muted : (isPrismDesign ? _prismDesign.tableHover : (root.isDark ? constants.themeColors.tableHoverDark : constants.themeColors.tableHoverLight))
    readonly property color alternateRowColor: isPrismDesign ? _prismDesign.alternateRow : (root.isDark ? constants.themeColors.alternateRowDark : constants.themeColors.alternateRowLight)
    readonly property color scrollTrackColor: isPrismDesign ? _prismDesign.scrollTrack : (root.isDark ? constants.themeColors.scrollTrackDark : constants.themeColors.scrollTrackLight)
    readonly property color scrollHandleColor: isPrismDesign ? _prismDesign.scrollHandle : (root.isDark ? constants.themeColors.scrollHandleDark : constants.themeColors.scrollHandleLight)
    readonly property color scrollHandleHoverColor: isPrismDesign ? _prismDesign.scrollHandleHover : (root.isDark ? constants.themeColors.scrollHandleHoverDark : constants.themeColors.scrollHandleHoverLight)
    readonly property color tableBgColor: isNeo ? _neo.surface : (isPrismDesign ? _prismDesign.tableBg : (root.isDark ? constants.themeColors.tableBgDark : constants.themeColors.tableBgLight))

    // ==================== Foreground Colors 前景色 ====================
    readonly property color foregroundColor: isNeo ? _neo.foreground : (isPrismDesign ? _prismDesign.foreground : (root.isDark ? constants.themeColors.foregroundDark : constants.themeColors.foregroundLight))
    readonly property color secondaryForeground: isNeo ? _neo.secondaryForeground : (isPrismDesign ? _prismDesign.secondaryForeground : (root.isDark ? constants.themeColors.secondaryForegroundDark : constants.themeColors.secondaryForegroundLight))
    readonly property color tertiaryForeground: isNeo ? _neo.secondaryForeground : (isPrismDesign ? _prismDesign.tertiaryForeground : (root.isDark ? constants.themeColors.tertiaryForegroundDark : constants.themeColors.tertiaryForegroundLight))
    readonly property color disabledForeground: isPrismDesign ? _prismDesign.disabledForeground : (root.isDark ? constants.themeColors.disabledForegroundDark : constants.themeColors.disabledForegroundLight)
    readonly property color accentForeground: isNeo ? _neo.primaryForeground : (isPrismDesign ? _prismDesign.primaryForeground : constants.themeColors.accentForeground)

    // ==================== Border Colors 边框色 ====================
    readonly property color borderColor: isNeo ? _neo.border : (isPrismDesign ? _prismDesign.border : (root.isDark ? constants.themeColors.borderDark : constants.themeColors.borderLight))
    readonly property color borderLightColor: isNeo ? _neo.border : (isPrismDesign ? _prismDesign.borderLight : (root.isDark ? constants.themeColors.borderLightDark : constants.themeColors.borderLightLight))
    readonly property color borderStrongColor: isNeo ? _neo.border : (isPrismDesign ? _prismDesign.borderStrong : (root.isDark ? constants.themeColors.borderStrongDark : constants.themeColors.borderStrongLight))
    readonly property color dividerColor: isNeo ? _neo.border : (isPrismDesign ? _prismDesign.divider : (root.isDark ? constants.themeColors.dividerDark : constants.themeColors.dividerLight))

    // ==================== Interaction Colors 交互色 ====================
    readonly property color hoverColor: isNeo ? _neo.muted : (isPrismDesign ? _prismDesign.hover : (root.isDark ? constants.themeColors.hoverDark : constants.themeColors.hoverLight))
    readonly property color pressedColor: isNeo ? Qt.darker(_neo.surface, 1.08) : (isPrismDesign ? _prismDesign.pressed : (root.isDark ? constants.themeColors.pressedDark : constants.themeColors.pressedLight))
    readonly property color disabledColor: isNeo ? _neo.muted : (isPrismDesign ? _prismDesign.disabled : (root.isDark ? constants.themeColors.disabledDark : constants.themeColors.disabledLight))
    readonly property color selectedColor: isPrismDesign ? _prismDesign.selected : (root.isDark ? constants.themeColors.selectedDark : constants.themeColors.selectedLight)
    readonly property color starColor: constants.themeColors.star
    readonly property color infoAccentColor: root.isDark ? constants.themeColors.infoAccentDark : constants.themeColors.infoAccentLight

    // ==================== Shadow Colors 阴影色 ====================
    readonly property color shadowColor: isPrismDesign ? _prismDesign.shadow : (root.isDark ? constants.themeColors.shadowDark : constants.themeColors.shadowLight)
    readonly property color shadowStrongColor: isPrismDesign ? _prismDesign.shadowStrong : (root.isDark ? constants.themeColors.shadowStrongDark : constants.themeColors.shadowStrongLight)
}
