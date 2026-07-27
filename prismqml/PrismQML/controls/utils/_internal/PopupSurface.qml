// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import "../../../effects"
import QtQuick.Effects
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

Item {
    id: surface

    required property int outerWidth
    required property int outerHeight
    required property int popupWidth
    required property int popupHeight
    required property int popupRadius
    required property color popupBackground
    required property int popupBorderWidth
    required property color popupBorderColor
    required property color popupShadowColor
    required property int popupShadowBlur
    required property int popupShadowOffset
    required property real clipHeight
    required property real panelScale

    default property alias popupContent: contentContainer.data

    objectName: "_popupSurface"
    width: outerWidth
    height: outerHeight
    opacity: Enums.opacityLevel.invisible

    // Shadow Layer 阴影层 (z: background to ensure it's behind popupPanel)
    // Sync opacity with popupPanel for smooth fade animation 与面板同步透明度实现平滑淡入
    // Fluent: 模糊阴影; neo: 硬阴影(偏移纯色矩形)
    RectangularShadow {
        z: Enums.zIndex.background
        x: clipContainer.x
        y: clipContainer.y
        width: clipContainer.width
        height: clipContainer.height
        radius: surface.popupRadius
        color: surface.popupShadowColor
        blur: surface.popupShadowBlur
        offset.x: 0
        offset.y: surface.popupShadowOffset
        visible: !Enums.isNeobrutalism
    }

    // neo 硬阴影: 偏移纯色矩形(弹层用 explicit 几何, 不用 NeoShadow 的 target)
    Rectangle {
        z: Enums.zIndex.background
        visible: Enums.isNeobrutalism
        x: clipContainer.x + Enums.neo.shadowOffset
        y: clipContainer.y + Enums.neo.shadowOffset
        width: clipContainer.width
        height: clipContainer.height
        radius: surface.popupRadius
        color: Enums.neo.shadowColor
    }

    // Clip container for drop-down animation 下拉动画裁剪容器
    Item {
        id: clipContainer

        x: Enums.popupMetrics.panelOffset
        y: Enums.popupMetrics.panelOffset
        width: surface.popupWidth
        height: surface.clipHeight
        clip: true

        // Popup panel 弹出面板
        Rectangle {
            id: popupPanel

            width: surface.popupWidth
            height: surface.popupHeight
            radius: surface.popupRadius
            color: surface.popupBackground
            border.width: surface.popupBorderWidth
            border.color: surface.popupBorderColor
            // [Anim C] Uniform scale, top-center origin (iOS spring style)
            transform: Scale {
                origin.x: popupPanel.width / 2
                origin.y: 0
                xScale: surface.panelScale
                yScale: surface.panelScale
            }

            // Content container 内容容器
            Item {
                id: contentContainer

                objectName: "_popupContent"
                anchors.fill: parent
                anchors.margins: Enums.spacing.xs
                // Keep delegates and animated loaders inside the popup padding.
                // 将代理项和动画 Loader 限制在弹层内边距以内。
                clip: true
            }
        }
    }
}
