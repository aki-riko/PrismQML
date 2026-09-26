// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// HeaderMetrics - Expander header measurement 展开器头部度量
// Owns the width/height math so HeaderContent only keeps header visuals.
// 单独持有宽高计算, 让 HeaderContent 只保留头部视觉与交互。
// All widths derive from the host width only; never from the title column itself,
// otherwise the column width and the text width would form a dependency loop.
// 所有宽度只由宿主宽度推导, 绝不读取标题列自身, 否则列宽与文本宽会形成依赖循环。
QtObject {
    id: metrics

    // ==================== Required Props 必需属性 ====================
    required property var expanderControl
    required property real hostWidth
    required property real titleLineHeight
    required property real contentLineHeight
    required property bool hasContent
    required property bool hasHeaderContent
    required property real headerContentWidth

    // ==================== Readonly State 只读状态 ====================
    // Expand button, its gap and the icon column 展开按钮、其间距与图标列
    readonly property real trailingWidth: Enums.controlSize.expanderIconSize
        + (expanderControl.icon !== ""
            ? (Enums.iconSize.m + Enums.spacing.xl) : 0)
        + (hasHeaderContent ? Enums.spacing.xl : 0)
        + Enums.spacing.m
    // Inner width left for the title column 标题列可用的内部宽度
    readonly property real textColumnWidth: Math.max(0,
        hostWidth - Enums.spacing.xl * 2 - trailingWidth - headerContentWidth)
    // Text block height, always reserved from the typography line box
    // 文本块高度: 始终按字体行高预留, 只有换行时才会因多行而变高
    readonly property real textBlockHeight: titleLineHeight
        + (hasContent ? contentLineHeight : 0)
    // Two-line headers keep their historical 72px, wrapped text may exceed it
    // 两行头部保持历史 72px, 换行超出后按实际行高自适应
    readonly property real minHeight: hasContent ? 72 : 48
    readonly property real headerHeight: Math.max(minHeight, textBlockHeight)
}
