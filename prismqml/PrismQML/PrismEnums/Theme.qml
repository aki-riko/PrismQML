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
    // Skin flags select palettes while theme remains the light/dark axis.
    // 皮肤标志选择调色板，theme 仍独立控制明暗。
    property bool isNeo: false
    property bool isTicket: false
    property bool isNeumorphism: false
    required property color accentColor
    required property color accentColorLight
    required property color accentColorDark
    required property var constants

    // Skin palettes 皮肤调色板快捷引用
    readonly property QtObject _neo: constants.neoColors
    readonly property QtObject _ticket: constants.ticketColors
    readonly property QtObject _neu: constants.neumorphismColors

    // ==================== Background Colors 背景色 ====================
    readonly property color backgroundColor: isNeo ? _neo.background : (isNeumorphism ? _neu.background : (isTicket ? _ticket.background : (root.isDark ? constants.themeColors.backgroundDark : constants.themeColors.backgroundLight)))
    readonly property color surfaceColor: isNeo ? _neo.surface : (isNeumorphism ? _neu.surface : (isTicket ? _ticket.surface : (root.isDark ? constants.themeColors.surfaceDark : constants.themeColors.surfaceLight)))
    readonly property color cardColor: isNeo ? _neo.surface : (isNeumorphism ? _neu.surface : (isTicket ? _ticket.surface : (root.isDark ? constants.themeColors.cardDark : constants.themeColors.cardLight)))
    readonly property color toastCardColor: isNeo ? _neo.surface : (isNeumorphism ? _neu.surface : (isTicket ? _ticket.surface : (root.isDark ? constants.themeColors.toastCardDark : constants.themeColors.toastCardLight)))
    readonly property color dialogColor: isNeo ? _neo.surface : (isNeumorphism ? _neu.surface : (isTicket ? _ticket.surface : (root.isDark ? constants.themeColors.dialogDark : constants.themeColors.dialogLight)))
    readonly property color headerColor: isNeo ? _neo.background : (isNeumorphism ? _neu.background : (isTicket ? _ticket.background : (root.isDark ? constants.themeColors.headerDark : constants.themeColors.headerLight)))
    readonly property color tableHoverColor: isNeo ? _neo.muted : (isNeumorphism ? _neu.hover : (isTicket ? _ticket.muted : (root.isDark ? constants.themeColors.tableHoverDark : constants.themeColors.tableHoverLight)))
    readonly property color alternateRowColor: isNeumorphism ? _neu.hover : (isTicket ? _ticket.muted : (root.isDark ? constants.themeColors.alternateRowDark : constants.themeColors.alternateRowLight))
    readonly property color scrollTrackColor: isNeumorphism ? _neu.muted : (isTicket ? _ticket.muted : (root.isDark ? constants.themeColors.scrollTrackDark : constants.themeColors.scrollTrackLight))
    readonly property color scrollHandleColor: isNeumorphism ? _neu.indicator : (isTicket ? _ticket.divider : (root.isDark ? constants.themeColors.scrollHandleDark : constants.themeColors.scrollHandleLight))
    readonly property color scrollHandleHoverColor: isNeumorphism ? _neu.indicatorHover : (isTicket ? _ticket.border : (root.isDark ? constants.themeColors.scrollHandleHoverDark : constants.themeColors.scrollHandleHoverLight))
    readonly property color tableBgColor: isNeo ? _neo.surface : (isNeumorphism ? _neu.surface : (isTicket ? _ticket.surface : (root.isDark ? constants.themeColors.tableBgDark : constants.themeColors.tableBgLight)))

    // ==================== Foreground Colors 前景色 ====================
    readonly property color foregroundColor: isNeo ? _neo.foreground : (isNeumorphism ? _neu.foreground : (isTicket ? _ticket.foreground : (root.isDark ? constants.themeColors.foregroundDark : constants.themeColors.foregroundLight)))
    readonly property color secondaryForeground: isNeo ? _neo.secondaryForeground : (isNeumorphism ? _neu.secondaryForeground : (isTicket ? _ticket.secondaryForeground : (root.isDark ? constants.themeColors.secondaryForegroundDark : constants.themeColors.secondaryForegroundLight)))
    readonly property color tertiaryForeground: isNeo ? _neo.secondaryForeground : (isNeumorphism ? _neu.secondaryForeground : (isTicket ? _ticket.secondaryForeground : (root.isDark ? constants.themeColors.tertiaryForegroundDark : constants.themeColors.tertiaryForegroundLight)))
    readonly property color disabledForeground: isNeumorphism ? _neu.disabledForeground : (isTicket ? _ticket.disabledForeground : (root.isDark ? constants.themeColors.disabledForegroundDark : constants.themeColors.disabledForegroundLight))
    readonly property color accentForeground: isNeo ? _neo.primaryForeground : (isNeumorphism ? _neu.primaryForeground : (isTicket ? _ticket.primaryForeground : constants.themeColors.accentForeground))

    // ==================== Border Colors 边框色 ====================
    readonly property color borderColor: isNeo ? _neo.border : (isNeumorphism ? Qt.rgba(0, 0, 0, 0) : (isTicket ? _ticket.border : (root.isDark ? constants.themeColors.borderDark : constants.themeColors.borderLight)))
    readonly property color borderLightColor: isNeo ? _neo.border : (isNeumorphism ? Qt.rgba(0, 0, 0, 0) : (isTicket ? _ticket.divider : (root.isDark ? constants.themeColors.borderLightDark : constants.themeColors.borderLightLight)))
    readonly property color borderStrongColor: isNeo ? _neo.border : (isNeumorphism ? Qt.rgba(0, 0, 0, 0) : (isTicket ? _ticket.border : (root.isDark ? constants.themeColors.borderStrongDark : constants.themeColors.borderStrongLight)))
    readonly property color dividerColor: isNeo ? _neo.border : (isNeumorphism ? _neu.divider : (isTicket ? _ticket.divider : (root.isDark ? constants.themeColors.dividerDark : constants.themeColors.dividerLight)))

    // ==================== Interaction Colors 交互色 ====================
    readonly property color hoverColor: isNeo ? _neo.muted : (isNeumorphism ? _neu.hover : (isTicket ? _ticket.muted : (root.isDark ? constants.themeColors.hoverDark : constants.themeColors.hoverLight)))
    readonly property color pressedColor: isNeo ? Qt.darker(_neo.surface, 1.08) : (isNeumorphism ? _neu.pressed : (isTicket ? Qt.darker(_ticket.muted, 1.06) : (root.isDark ? constants.themeColors.pressedDark : constants.themeColors.pressedLight)))
    readonly property color disabledColor: isNeo ? _neo.muted : (isNeumorphism ? _neu.disabledSurface : (isTicket ? _ticket.muted : (root.isDark ? constants.themeColors.disabledDark : constants.themeColors.disabledLight)))
    readonly property color selectedColor: isNeumorphism ? _neu.selected : (isTicket ? Qt.rgba(_ticket.primary.r, _ticket.primary.g, _ticket.primary.b, 0.16) : (root.isDark ? constants.themeColors.selectedDark : constants.themeColors.selectedLight))
    readonly property color starColor: isNeumorphism ? _neu.warning : (isTicket ? _ticket.warning : constants.themeColors.star)
    readonly property color infoAccentColor: isNeumorphism ? _neu.info : (isTicket ? _ticket.info : (root.isDark ? constants.themeColors.infoAccentDark : constants.themeColors.infoAccentLight))

    // ==================== Shadow Colors 阴影色 ====================
    readonly property color shadowColor: isNeumorphism ? _neu.shadowDark : (isTicket ? Qt.rgba(0, 0, 0, 0) : (root.isDark ? constants.themeColors.shadowDark : constants.themeColors.shadowLight))
    readonly property color shadowStrongColor: isNeumorphism ? _neu.shadowDark : (isTicket ? Qt.rgba(0, 0, 0, 0) : (root.isDark ? constants.themeColors.shadowStrongDark : constants.themeColors.shadowStrongLight))
}
