// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// NeumorphicInsetLayer - Lazily loaded concave edge layer 按需加载的新拟态内凹边缘层
Item {
    id: layer

    // ==================== Readonly State 只读状态 ====================
    readonly property Item control: parent
    readonly property Item target: control ? control.target : null

    // ==================== Size 尺寸 ====================
    anchors.fill: parent

    // ==================== Content 内容 ====================
    // Reparent the painted layer onto the opaque target so the inset remains visible.
    // 将绘制层重定父级到不透明目标上，保证内凹边缘可见。
    Item {
        objectName: "_neumorphicInsetLayer"
        parent: layer.target ? layer.target : layer
        anchors.fill: parent
        z: Enums.zIndex.controlsAbove
        clip: true

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: layer.control ? layer.control._edgeSize : 0
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0; color: layer.control ? layer.control.darkColor : Enums.transparent }
                GradientStop { position: 1; color: Enums.transparent }
            }
        }

        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: layer.control ? layer.control._edgeSize : 0
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: layer.control ? layer.control.darkColor : Enums.transparent }
                GradientStop { position: 1; color: Enums.transparent }
            }
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: layer.control ? layer.control._edgeSize : 0
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0; color: Enums.transparent }
                GradientStop { position: 1; color: layer.control ? layer.control.lightColor : Enums.transparent }
            }
        }

        Rectangle {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: layer.control ? layer.control._edgeSize : 0
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: Enums.transparent }
                GradientStop { position: 1; color: layer.control ? layer.control.lightColor : Enums.transparent }
            }
        }
    }
}
