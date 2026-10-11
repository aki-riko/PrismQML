// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."
import "../Label"
import "../../icons"
import "../../utils"

// Avatar - Avatar component 头像组件
// Props: source(图片路径), text(文字), size(尺寸)
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string source: ""
    property string text: ""
    property int size: 40

    // PersonPicture extensions 人物头像扩展能力
    property string initials: ""     // Explicit initials, may be multi-character 显式首字母, 可多字符
    property int badgeNumber: 0      // Overlay badge count 叠加数字徽章
    property string badgeGlyph: ""   // Overlay badge icon 叠加图标徽章
    property bool isGroup: false     // Group picture semantics 群组头像语义

    // ==================== Readonly State 只读状态 ====================
    // Empty initials fall back to the historical single-character behaviour.
    // initials 为空时回落到既有的单字符行为。
    readonly property string _displayInitials: initials !== ""
        ? initials.slice(0, Enums.badge.personPictureInitialsLength)
        : (text.length > 0 ? text.charAt(0).toUpperCase() : "")
    readonly property bool _multiInitials: _displayInitials.length > 1
    readonly property bool _hasBadge: badgeNumber > 0 || badgeGlyph !== ""
    readonly property string _placeholderIcon:
        isGroup ? Enums.icon.people : Enums.icon.person
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
    // An avatar is a person or group label, so it stays static text; the name
    // prefers explicit initials over the fallback text a sighted user reads.
    // 头像是人物或群组标签，故按静态文本处理；名称优先显式首字母，其次回退可见文本。
    A11ySurface {
        target: control
        role: Enums.accessibility.role_statictext
        name: control.initials !== "" ? control.initials : control.text
    }

    // Text avatar 文字头像
    // Explicit initials without a text fallback share this label: its own `text`
    // now carries the resolved initials.
    // 无 text 回退的显式首字母复用该标签: 标签自身的 `text` 已是解析后的首字母。
    Label {
        objectName: "avatarInitials"
        type: Enums.label.type_body
        anchors.centerIn: parent
        text: control._displayInitials
        font.pixelSize: size * (control._multiInitials
                                ? Enums.badge.personPictureMultiInitialsScale
                                : Enums.badge.personPictureInitialsScale)
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
        objectName: "avatarPlaceholder"
        anchors.centerIn: parent
        // Keep the historical empty icon whenever initials are rendered, so the
        // renderer set of a text avatar is unchanged.
        // 渲染首字母时保持历史上的空图标, 使文字头像的渲染器集合不变。
        icon: (source === "" && (text !== "" || initials !== ""))
              ? "" : control._placeholderIcon
        iconSize: size * 0.5
        color: control._avatarContentColor
        visible: control.source === "" && control.text === ""
    }

    // Badge overlay 叠加徽章
    // Created only when a badge is requested, so a plain avatar keeps exactly the
    // renderer set it had before. 仅在需要徽章时创建, 普通头像保持改动前的渲染器集合。
    Loader {
        objectName: "avatarBadgeLoader"
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        active: control._hasBadge

        sourceComponent: Badge {
            objectName: "avatarBadge"
            count: control.badgeNumber
            icon: control.badgeGlyph
        }
    }
}
