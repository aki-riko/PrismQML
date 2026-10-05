// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."
import "../Label"
import "../../icons"

// Avatar - Avatar component 头像组件
// Props: source(图片路径), text(文字), size(尺寸)
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string source: ""
    property string text: ""
    property int size: 40

    // ==================== Readonly State 只读状态 ====================
    readonly property color _avatarBackground: source !== "" ? Enums.transparent : Enums.accentColor
    readonly property real _avatarBorderWidth: Enums.hasOutlinedSurfaces
                                               ? Enums.surfaceBorderWidth(Enums.border.thin) : 0
    readonly property color _avatarBorderColor: Enums.hasOutlinedSurfaces
                                                 ? Enums.stateColor.border : Enums.transparent
    readonly property color _avatarContentColor: Enums.accentForeground
    // Circular bitmap masking runs through the layer path, which the Software
    // scene graph does not execute; that backend keeps the plain image draw.
    // 圆形位图遮罩依赖层路径, 软件场景图后端不执行该路径, 该后端保留普通图片绘制。
    readonly property bool _avatarMaskSupported: GraphicsInfo.api !== GraphicsInfo.Software
                                                 && GraphicsInfo.api !== GraphicsInfo.Unknown
                                                 && GraphicsInfo.api !== GraphicsInfo.Null

    // ==================== Public Methods 公开方法 ====================
    // Set avatar size 设置头像尺寸
    function setRadius(r) {
        size = r * 2
    }

    width: size
    height: size
    radius: size / 2
    color: control._avatarBackground
    antialiasing: true
    // Avatar boundary for non-Fluent skins 非 Fluent 皮肤头像边界
    border.width: control._avatarBorderWidth
    border.color: control._avatarBorderColor

    // Text avatar 文字头像
    Label {
        type: Enums.label.type_body
        anchors.centerIn: parent
        text: control.text.length > 0 ? control.text.charAt(0).toUpperCase() : ""
        font.pixelSize: size * 0.4
        font.bold: true
        color: control._avatarContentColor
        visible: source === "" && text !== ""
    }

    // Image avatar with circular layer mask 圆形层遮罩图片头像
    // A plain Image paints as soon as it is ready and sized, so no manual
    // repaint trigger is needed when the host becomes visible later. The layer
    // texture is allocated at device resolution, so the bitmap is rasterized
    // 1:1 with the screen instead of being upscaled from logical pixels.
    // 普通 Image 在就绪且有尺寸时即绘制, 宿主稍后可见时无需手工触发重绘。
    // 层纹理按设备分辨率分配, 位图与屏幕 1:1 光栅化, 不再由逻辑像素放大。
    Image {
        id: avatarImage

        anchors.fill: parent
        visible: control.source !== ""
        source: control.source
        asynchronous: true
        cache: true
        mipmap: true
        smooth: true
        fillMode: Image.PreserveAspectCrop
        layer.enabled: control._avatarMaskSupported && status === Image.Ready
        layer.smooth: true
        layer.effect: MultiEffect {
            maskEnabled: true
            maskThresholdMin: Enums.mask.thresholdMin
            maskSpreadAtMin: Enums.mask.spreadFull
            maskSource: ShaderEffectSource {
                sourceItem: Rectangle {
                    width: avatarImage.width
                    height: avatarImage.height
                    radius: avatarImage.width / 2
                    antialiasing: true
                }
                smooth: true
            }
        }
    }

    // Placeholder when no content 无内容时的占位符
    Icon {
        anchors.centerIn: parent
        icon: control.source === "" && control.text !== "" ? "" : Enums.icon.person
        iconSize: size * 0.5
        color: control._avatarContentColor
        visible: control.source === "" && control.text === ""
    }
}
