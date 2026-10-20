// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

// ButtonStyle - Shared pure button color calculations 共享按钮纯颜色计算

.pragma library

.import "../../utils/_internal/ContrastInk.js" as ContrastInk

function _defaultBackgroundColor(effectiveEnabled, hovered, pressed, stateColor) {
    if (!effectiveEnabled) return stateColor.controlBgDisabled
    if (pressed) return stateColor.controlBgPressed
    if (hovered) return stateColor.controlBgHover
    return stateColor.controlBg
}

function backgroundColor(style, level, effectiveEnabled, hovered, pressed,
                         isToggleChecked, isVintageTicket, isNeumorphism,
                         button, stateColor, statusLevel, accentColor, cardColor) {
    if (isToggleChecked) {
        if (style === button.style_primary) {
            if (!effectiveEnabled) {
                return isVintageTicket ? stateColor.disabledBg : stateColor.disabled
            }
            if (pressed) return stateColor.controlBgPressed
            if (hovered) return stateColor.controlBgHover
            return cardColor
        }
        if (!effectiveEnabled) {
            return isVintageTicket ? stateColor.disabledBg : stateColor.disabled
        }
        if (pressed) return Qt.darker(accentColor, 1.1)
        if (hovered) return Qt.lighter(accentColor, 1.1)
        return accentColor
    }

    switch (style) {
    case button.style_primary:
        if (!effectiveEnabled) return stateColor.primaryDisabled
        if (pressed) return Qt.darker(accentColor, 1.1)
        if (hovered) return Qt.lighter(accentColor, 1.1)
        return accentColor
    case button.style_transparent:
    case button.style_text:
    case button.style_hyperlink:
        if (!effectiveEnabled) return stateColor.controlBgTransparent
        if (pressed) return stateColor.transparentPressed
        if (hovered) return stateColor.transparentHover
        return stateColor.controlBgTransparent
    case button.style_filled:
        var statusColor = statusLevel.getColorByLevel(level)
        if (!effectiveEnabled) {
            // Preserve level hue for disabled filled buttons. 禁用填充按钮保留级别色相。
            return Qt.rgba(statusColor.r, statusColor.g, statusColor.b,
                           stateColor.filledDisabledAlpha)
        }
        if ((isVintageTicket || isNeumorphism) && pressed) {
            return Qt.darker(statusColor, 1.12)
        }
        if ((isVintageTicket || isNeumorphism) && hovered) {
            return Qt.lighter(statusColor, 1.12)
        }
        if (pressed) return stateColor.filledPressed
        if (hovered) return stateColor.filledHover
        return statusColor
    case button.style_gradient:
        if (!effectiveEnabled) {
            return isVintageTicket ? stateColor.disabledBg : stateColor.disabled
        }
        if (pressed) return Qt.darker(accentColor, 1.1)
        if (hovered) return Qt.lighter(accentColor, 1.1)
        return accentColor
    default:
        return _defaultBackgroundColor(
            effectiveEnabled, hovered, pressed, stateColor)
    }
}

function _neoBorderColor(style, button, transparent, neo) {
    if (style === button.style_transparent ||
            style === button.style_text ||
            style === button.style_hyperlink) {
        return transparent
    }
    return neo.borderColor
}

function _ticketBorderColor(style, button, transparent, ticket) {
    if (style === button.style_transparent ||
            style === button.style_text ||
            style === button.style_hyperlink) {
        return transparent
    }
    return ticket.borderColor
}

function borderColor(style, level, effectiveEnabled, isToggleChecked,
                     isNeobrutalism, isVintageTicket, button, stateColor,
                     statusLevel, accentColor, transparent, neo, ticket) {
    if (isNeobrutalism) {
        return _neoBorderColor(style, button, transparent, neo)
    }
    if (isVintageTicket) {
        return _ticketBorderColor(style, button, transparent, ticket)
    }
    if (isToggleChecked && style === button.style_primary) return accentColor

    switch (style) {
    case button.style_text:
    case button.style_hyperlink:
    case button.style_primary:
    case button.style_gradient:
        return transparent
    case button.style_filled:
        if (!effectiveEnabled) return stateColor.divider
        return statusLevel.getColorByLevel(level)
    default:
        if (!effectiveEnabled) return stateColor.border
        return stateColor.borderStrong
    }
}

function _isAccentStyle(style, button) {
    return style === button.style_primary ||
           style === button.style_filled ||
           style === button.style_gradient
}

function _neoTextColor(style, effectiveEnabled, button, opacityLevel, neo) {
    if (_isAccentStyle(style, button)) {
        if (!effectiveEnabled) {
            return Qt.rgba(neo.primaryForeground.r, neo.primaryForeground.g,
                           neo.primaryForeground.b, opacityLevel.heavy)
        }
        return neo.primaryForeground
    }
    if (style === button.style_hyperlink) return neo.primary
    if (!effectiveEnabled) return neo.secondaryForeground
    return neo.foreground
}

function textColor(style, level, effectiveEnabled, hovered, pressed,
                   isToggleChecked, isNeobrutalism, button, textColorTokens,
                   statusLevel, accentColor, accentForeground, opacityLevel,
                   neo, isVisited, visitedLinkColor, bgColor, onLightInk) {
    if (isNeobrutalism) {
        return _neoTextColor(
            style, effectiveEnabled, button, opacityLevel, neo)
    }
    if (isToggleChecked) {
        if (style === button.style_primary) {
            if (!effectiveEnabled) return textColorTokens.disabled
            return accentColor
        }
        if (!effectiveEnabled) return textColorTokens.tertiary
        if (pressed) return textColorTokens.strong
        return ContrastInk.onFill(bgColor, accentForeground, onLightInk)
    }

    switch (style) {
    case button.style_primary:
    case button.style_gradient:
    case button.style_filled:
        if (!effectiveEnabled) return textColorTokens.tertiary
        // A filled surface can carry any semantic or accent colour, so keep the
        // preferred ink only while it stays legible and otherwise fall back to the
        // light-surface ink. Dark semantic tokens are pastels meant as foreground
        // accents, so white text on them is unreadable without this guard.
        // 填充表面可能承载任意语义色或主色，因此仅在首选墨色仍可读时保留，否则退回
        // 浅色表面墨色。深色语义 token 是作为前景强调色的粉彩色，缺此保护时白字不可读。
        return ContrastInk.onFill(bgColor, accentForeground, onLightInk)
    case button.style_hyperlink:
        if (!effectiveEnabled) return textColorTokens.disabled
        // A visited hyperlink keeps the same hover/press derivation, only the
        // resting hue changes. 已访问超链接沿用同一套悬浮/按压推导，仅静息色相改变。
        var linkColor = isVisited ? visitedLinkColor : accentColor
        if (pressed) return Qt.darker(linkColor, 1.2)
        if (hovered) return Qt.lighter(linkColor, 1.1)
        return linkColor
    case button.style_text:
        var statusColor = statusLevel.getColorByLevel(level)
        if (!effectiveEnabled) return textColorTokens.disabled
        if (pressed) return Qt.darker(statusColor, 1.2)
        if (hovered) return Qt.lighter(statusColor, 1.1)
        return statusColor
    default:
        if (!effectiveEnabled) return textColorTokens.disabled
        if (pressed) return textColorTokens.tertiary
        return textColorTokens.primary
    }
}

function snapshot(style, level, effectiveEnabled, hovered, pressed,
                  isToggleChecked, isNeobrutalism, isVintageTicket,
                  isNeumorphism, button, stateColor, textColorTokens,
                  statusLevel, accentColor, cardColor, accentForeground,
                  transparent, opacityLevel, neo, ticket,
                  isVisited, visitedLinkColor, onLightInk) {
    // The fill is resolved once so the ink can be validated against the exact
    // colour that will be painted behind it, including hover and press states.
    // 填充色只解析一次，使墨色可针对真正被绘制在背后的颜色校验，含悬浮与按压态。
    var bgColor = backgroundColor(
        style, level, effectiveEnabled, hovered, pressed, isToggleChecked,
        isVintageTicket, isNeumorphism, button, stateColor, statusLevel,
        accentColor, cardColor)
    return {
        effectiveEnabled: effectiveEnabled,
        isToggleChecked: isToggleChecked,
        bgColor: bgColor,
        borderColor: borderColor(
            style, level, effectiveEnabled, isToggleChecked, isNeobrutalism,
            isVintageTicket, button, stateColor, statusLevel, accentColor,
            transparent, neo, ticket),
        textColor: textColor(
            style, level, effectiveEnabled, hovered, pressed, isToggleChecked,
            isNeobrutalism, button, textColorTokens, statusLevel, accentColor,
            accentForeground, opacityLevel, neo, isVisited, visitedLinkColor,
            bgColor, onLightInk)
    }
}
