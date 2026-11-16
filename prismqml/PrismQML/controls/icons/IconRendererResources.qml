// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

pragma Singleton
import QtQuick
import QtQuick.Effects
import "../.."
import "../../effects"

// IconRendererResources - Shared icon renderer factories 共享图标渲染器工厂
QtObject {
    // ==================== Public Props 公开属性 ====================
    readonly property Component textIconComponent: Component {
        Text {
            anchors.centerIn: parent
            text: parent.iconControl.icon
            font.pixelSize: parent.iconControl.iconSize
            font.family: Enums.fontFamily
            color: parent.iconControl.color
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    // Tinted images draw through one ShaderEffect that samples the Image texture
    // directly. The former layer.effect rendered every icon into its own offscreen
    // texture first: about 0.28ms of first-frame time per icon, measured on D3D11.
    // 着色图片经一个直接采样 Image 纹理的 ShaderEffect 绘制。原 layer.effect 会先把每个
    // 图标渲染进各自的离屏纹理：D3D11 实测每个图标首帧多约 0.28ms。
    readonly property Component imageIconComponent: Component {
        Item {
            id: imageHost

            readonly property var iconControl: parent.iconControl
            readonly property bool _tinted: iconControl.themeAware
                && imageIcon.status === Image.Ready

            anchors.centerIn: parent
            width: iconControl.iconSize
            height: iconControl.iconSize

            Image {
                id: imageIcon

                anchors.fill: parent
                source: imageHost.iconControl._resolvedSource
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: !imageHost.iconControl.isSvgIcon
                asynchronous: !imageHost.iconControl.isSvgIcon
                sourceSize: imageHost.iconControl.isSvgIcon
                    ? Qt.size(imageHost.iconControl.iconSize * 2,
                              imageHost.iconControl.iconSize * 2)
                    : Qt.size(0, 0)
                // The tint pass draws instead of the image 着色时由着色层代替原图绘制
                opacity: imageHost._tinted ? 0 : 1
            }

            ShaderEffect {
                readonly property var source: imageIcon
                readonly property color tintColor: imageHost.iconControl.color

                anchors.fill: parent
                visible: imageHost._tinted
                fragmentShader: Qt.resolvedUrl("../../shaders/icon_tint.frag.qsb")
            }
        }
    }

    readonly property Component avatarIconComponent: Component {
        Item {
            id: avatarContainer

            width: parent.iconControl.iconSize
            height: parent.iconControl.iconSize
            anchors.centerIn: parent

            Image {
                id: avatarImage

                anchors.fill: parent
                source: avatarContainer.parent.iconControl._resolvedSource
                fillMode: Image.PreserveAspectCrop
                smooth: true
                mipmap: true
                asynchronous: true

                layer.enabled: avatarImage.status === Image.Ready
                layer.smooth: true
                layer.effect: MultiEffect {
                    maskEnabled: true
                    maskThresholdMin: 0.5
                    maskSpreadAtMin: 1.0
                    maskSource: ShaderEffectSource {
                        sourceItem: Rectangle {
                            width: avatarContainer.width
                            height: avatarContainer.height
                            radius: width / 2
                            antialiasing: true
                        }
                    }
                }
            }
        }
    }
}
