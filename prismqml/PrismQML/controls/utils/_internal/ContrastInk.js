// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

// ContrastInk - WCAG relative-luminance ink selection 对比度墨色选择
// Pure colour maths shared by filled surfaces so a label stays readable on any
// fill the palette can produce. 供填充型表面复用的纯颜色计算，使标签在调色板
// 能产出的任意填充色上都保持可读。

.pragma library

// ==================== Internal Methods 内部方法 ====================
function _linearize(component) {
    return component <= 0.03928
        ? component / 12.92
        : Math.pow((component + 0.055) / 1.055, 2.4)
}

// ==================== Public Methods 公开方法 ====================
// WCAG 2.1 relative luminance of an opaque colour. 不透明色的 WCAG 2.1 相对亮度。
function relativeLuminance(color) {
    return 0.2126 * _linearize(color.r)
        + 0.7152 * _linearize(color.g)
        + 0.0722 * _linearize(color.b)
}

// WCAG 2.1 contrast ratio between two opaque colours. 两不透明色的 WCAG 2.1 对比度。
function contrastRatio(first, second) {
    var a = relativeLuminance(first)
    var b = relativeLuminance(second)
    var lighter = Math.max(a, b)
    var darker = Math.min(a, b)
    return (lighter + 0.05) / (darker + 0.05)
}

// Keep the preferred ink while it stays legible on the fill, otherwise fall back
// to the supplied alternative. Passes currently-legible fills through untouched so
// a contrast fix never repaints a surface that was already compliant.
// 首选墨色在填充上仍可读时保持不变，否则退回备选墨色。已合规的填充原样透传，
// 使对比度修复不会重绘已达标的表面。
function onFill(fill, preferredInk, fallbackInk, minRatio) {
    var threshold = minRatio === undefined ? 4.5 : minRatio
    if (contrastRatio(preferredInk, fill) >= threshold) return preferredInk
    return fallbackInk
}