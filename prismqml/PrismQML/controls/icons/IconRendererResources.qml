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

    readonly property Component imageIconComponent: Component {
        Image {
            id: imageIcon

            anchors.centerIn: parent
            width: parent.iconControl.iconSize
            height: parent.iconControl.iconSize
            source: parent.iconControl._resolvedSource
            fillMode: Image.PreserveAspectFit
            smooth: true
            mipmap: !parent.iconControl.isSvgIcon
            asynchronous: !parent.iconControl.isSvgIcon
            sourceSize: parent.iconControl.isSvgIcon
                ? Qt.size(parent.iconControl.iconSize * 2, parent.iconControl.iconSize * 2)
                : Qt.size(0, 0)

            layer.enabled: imageIcon.status === Image.Ready
            layer.effect: ColorOverlay {
                color: imageIcon.parent.iconControl.color
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
