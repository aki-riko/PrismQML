// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// ParallaxViewContent - ParallaxView visual layer 视差视图视觉层
// Owns the background host and the source-driven offset math 承载背景宿主与滚动源驱动的位移计算
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Public Props 公开属性 ====================
    default property alias content: backgroundHost.data

    // ==================== Readonly State 只读状态 ====================
    readonly property var _source: host.source
    readonly property real _contentX: _sourceValue("contentX")
    readonly property real _contentY: _sourceValue("contentY")
    readonly property real _contentWidth: _sourceValue("contentWidth")
    readonly property real _contentHeight: _sourceValue("contentHeight")
    readonly property real _viewportWidth: _source ? _source.width : 0
    readonly property real _viewportHeight: _source ? _source.height : 0
    readonly property real horizontalProgress: _progress(true)
    readonly property real verticalProgress: _progress(false)
    readonly property real horizontalOffset:
        -horizontalProgress * host.horizontalShift
    readonly property real verticalOffset: -verticalProgress * host.verticalShift

    // ==================== Internal Methods 内部方法 ====================
    // Read one numeric source property defensively 防御式读取滚动源的数值属性
    function _sourceValue(name) {
        var source = _source
        if (!source) return 0
        var value = source[name]
        return typeof value === "number" && isFinite(value) ? value : 0
    }

    // Normalized range progress 归一化区间进度
    function _progress(horizontal) {
        var position = horizontal ? _contentX : _contentY
        var start = horizontal
            ? host.horizontalSourceStartOffset : host.verticalSourceStartOffset
        var end = horizontal
            ? host.horizontalSourceEndOffset : host.verticalSourceEndOffset
        var viewport = horizontal ? _viewportWidth : _viewportHeight
        var extent = horizontal ? _contentWidth : _contentHeight
        if (end <= start) end = start + Math.max(0, extent - viewport)
        var span = end - start
        if (span <= 0) return 0
        return Math.max(0, Math.min(1, (position - start) / span))
    }

    // ==================== Size 尺寸 ====================
    clip: host.clipContent

    // ==================== Content 内容 ====================
    // Shifted background host 位移后的背景宿主
    Item {
        id: backgroundHost
        objectName: "parallaxBackgroundHost"
        x: content.horizontalOffset
        y: content.verticalOffset
        width: content.width
        height: content.height
    }
}
