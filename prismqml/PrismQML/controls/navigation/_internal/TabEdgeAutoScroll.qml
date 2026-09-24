// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// TabEdgeAutoScroll - Frame-synced drag edge scrolling for TabWidget
// TabEdgeAutoScroll - TabWidget 拖拽边缘逐帧自动滚动
FrameAnimation {
    id: edgeAutoScroll

    // ==================== Required Props 必需属性 ====================
    required property Item host
    required property Flickable tabFlickable

    // ==================== Internal Methods 内部方法 ====================
    onTriggered: {
        if (!host._dragging) return
        var edgeMargin = 40
        // Scale the per-frame step by frame time for refresh-rate independence.
        // 按帧时长换算步长，保证不同刷新率下的滚动速度一致。
        var step = 480 * frameTime
        if (host.vertical) {
            // Vertical strips scroll on the Y axis with the same edge margin
            // 纵向条带在 Y 轴滚动, 边缘留白一致
            var visibleTop = tabFlickable.contentY
            var visibleBottom = visibleTop + tabFlickable.height
            var pointerY = host._dragPointerRowX
            if (pointerY < visibleTop + edgeMargin && tabFlickable.contentY > 0) {
                tabFlickable.contentY = Math.max(
                    0, tabFlickable.contentY - step)
            } else if (pointerY > visibleBottom - edgeMargin) {
                var maxY = Math.max(
                    0, tabFlickable.contentHeight - tabFlickable.height)
                tabFlickable.contentY = Math.min(
                    maxY, tabFlickable.contentY + step)
            }
            return
        }
        var visibleLeft = tabFlickable.contentX
        var visibleRight = visibleLeft + tabFlickable.width
        var pointerX = host._dragPointerRowX
        if (pointerX < visibleLeft + edgeMargin && tabFlickable.contentX > 0) {
            tabFlickable.contentX = Math.max(
                0, tabFlickable.contentX - step)
        } else if (pointerX > visibleRight - edgeMargin) {
            var maxX = Math.max(
                0, tabFlickable.contentWidth - tabFlickable.width)
            tabFlickable.contentX = Math.min(
                maxX, tabFlickable.contentX + step)
        }
    }
}
