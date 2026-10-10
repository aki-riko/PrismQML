// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal" as LayoutInternal

// ParallaxView - Scroll driven parallax background 滚动驱动视差背景
// Fluent ParallaxView parity: the background shifts against a scroll source
// 对齐 Fluent ParallaxView：背景相对滚动源反向位移
// The source may be any item exposing contentX / contentY (Flickable, ListView,
// ScrollArea). 滚动源可以是任何暴露 contentX / contentY 的项（Flickable、ListView、ScrollArea）。
// Shift semantics 位移语义: the background moves -progress * shift over the source
// range, where progress is 0 at the range start and 1 at the range end.
// 背景在滚动区间内位移 -progress * shift, progress 在区间起点为 0、终点为 1。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Scroll source 滚动源
    property Item source: null
    // Shift distances over the whole range 整个区间内的位移距离
    property real horizontalShift: 0
    property real verticalShift: 0
    // Source ranges driving the parallax 驱动视差的滚动区间
    property real horizontalSourceStartOffset: 0
    property real horizontalSourceEndOffset: 0
    property real verticalSourceStartOffset: 0
    property real verticalSourceEndOffset: 0
    // Clip the shifted background 裁剪位移后的背景
    property bool clipContent: true

    // Content 内容
    default property alias content: contentHolder.content

    // ==================== Readonly State 只读状态 ====================
    readonly property real horizontalProgress: parallaxContent.horizontalProgress
    readonly property real verticalProgress: parallaxContent.verticalProgress
    readonly property real horizontalOffset: parallaxContent.horizontalOffset
    readonly property real verticalOffset: parallaxContent.verticalOffset

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.flow.layout_implicit_width
    implicitHeight: Enums.flow.layout_implicit_height

    // ==================== Content 内容 ====================
    // Content holder keeps the entry free of the visual tree 内容持有者让入口不承载视觉树
    QtObject {
        id: contentHolder
        default property list<QtObject> content
    }

    LayoutInternal.ParallaxViewContent {
        id: parallaxContent
        objectName: "parallaxViewSurface"
        anchors.fill: parent
        host: control
        content: contentHolder.content
    }
}
