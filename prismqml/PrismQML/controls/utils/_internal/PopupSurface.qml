// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import "../../../effects"
import QtQuick.Effects
import QtQuick  // After library import: unprefixed native types stay unshadowed 置于库import后:去前缀后保原生类型不被库覆盖

Item {
    id: surface

    required property int outerWidth
    required property int outerHeight
    required property int popupWidth
    required property int popupHeight
    required property int contentPadding
    required property real panelOffset
    required property int popupRadius
    required property color popupBackground
    required property real popupBorderWidth
    required property color popupBorderColor
    required property color popupShadowColor
    required property int popupShadowBlur
    required property int popupShadowOffset
    required property real popupNeumorphicShadowBlur
    required property real popupNeumorphicShadowOffset
    required property real popupNeumorphicShadowSpread
    required property real clipHeight
    required property bool shadowVisible
    // PopupWindowCore passes a captured context because this surface can move
    // into a native window outside the original SkinScope tree.
    // PopupWindowCore 传入已捕获上下文，因为该表面可能移动到原始 SkinScope 树外的原生窗口。
    property var skinContext: Enums
    readonly property var _skin: skinContext || Enums
    readonly property var _prismSkinScopeContext: _skin
    property Item _interactionHost: null

    default property alias popupContent: contentContainer.data

    objectName: "_popupSurface"
    width: outerWidth
    height: outerHeight
    opacity: _skin.opacityLevel.invisible

    // Shadow Layer 阴影层 (z: background to ensure it's behind popupPanel)
    // Surface opacity and cover height animate independently.
    // 表面透明度与遮挡层高度独立动画。
    // Fluent uses one elevation shadow; neumorphism uses a paired shadow below.
    // Fluent 使用单层高度阴影；新拟态使用下方的双向阴影。
    RectangularShadow {
        objectName: "_popupShadow"
        z: _skin.zIndex.background
        x: clipContainer.x
        y: clipContainer.y + (surface.popupHeight - height) / 2
        width: popupPanel.width
        height: popupPanel.height
        radius: surface.popupRadius
        color: surface.popupShadowColor
        blur: surface.popupShadowBlur
        offset.x: 0
        offset.y: surface.popupShadowOffset
        visible: surface.shadowVisible && _skin.usesSoftElevation && !_skin.isNeumorphism
    }

    NeumorphicShadow {
        objectName: "_popupNeumorphicShadow"
        target: popupPanel
        offset: surface.popupNeumorphicShadowOffset
        blur: surface.popupNeumorphicShadowBlur
        spread: surface.popupNeumorphicShadowSpread
        z: _skin.zIndex.background
        anchors.fill: null
        x: clipContainer.x
        y: clipContainer.y + (surface.popupHeight - height) / 2
        width: popupPanel.width
        height: popupPanel.height
        visible: surface.shadowVisible && _skin.isNeumorphism
    }

    // Neobrutalism hard shadow; popup geometry stays explicit.
    // 新粗野硬阴影；弹层继续使用显式几何。
    Rectangle {
        objectName: "_popupNeoShadow"
        z: _skin.zIndex.background
        visible: surface.shadowVisible && _skin.isNeobrutalism
        x: clipContainer.x + _skin.neo.shadowOffset
        y: clipContainer.y + (surface.popupHeight - height) / 2 + _skin.neo.shadowOffset
        width: popupPanel.width
        height: popupPanel.height
        radius: surface.popupRadius
        color: _skin.neo.shadowColor
    }

    // Clip container for drop-down animation 下拉动画裁剪容器
    Item {
        id: clipContainer

        x: surface.panelOffset
        y: surface.panelOffset
        width: surface.popupWidth
        height: surface.popupHeight
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
            // Reveal the panel through a full-size mask whose visible height follows the container.
            // 使用与面板同尺寸的遮罩，仅让其可见高度跟随容器展开。
            layer.enabled: true
            layer.effect: MultiEffect {
                maskEnabled: true
                maskThresholdMin: 0.5
                maskSpreadAtMin: 1.0
                maskSource: ShaderEffectSource {
                    objectName: "_popupRevealMask"
                    live: true
                    smooth: true
                    sourceItem: Item {
                        width: popupPanel.width
                        height: popupPanel.height
                        clip: true

                        Rectangle {
                            width: parent.width
                            height: surface.clipHeight
                            color: _skin.textColor.primary
                        }
                    }
                }
            }
            Loader {
                objectName: "ticketPaperLoader"
                anchors.fill: parent
                active: _skin.isVintageTicket
                // Complete the surface before its popup can be destroyed. 在弹层可能销毁前同步完成表面创建。
                asynchronous: false
                source: Qt.resolvedUrl("../../../effects/TicketPaper.qml")
            }

            // Content container 内容容器
            Item {
                id: contentContainer

                objectName: "_popupContent"
                anchors.fill: parent
                anchors.margins: surface.contentPadding
                // Keep delegates and animated loaders inside the popup padding.
                // 将代理项和动画 Loader 限制在弹层内边距以内。
                clip: true
            }

        }
    }
}
