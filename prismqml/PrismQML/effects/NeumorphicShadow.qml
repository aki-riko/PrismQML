// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import ".."

// NeumorphicShadow - paired soft light/dark shadows 新拟态双向软阴影
// One reusable primitive provides convex and concave surfaces for all controls.
// 统一提供凸起与凹入表面，避免控件散落手写阴影。
Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    property Item target: parent
    property bool inset: false
    property bool pressed: false
    property bool accent: false
    property real offset: Enums.neumorphism.shadowOffset
    property real blur: Enums.neumorphism.shadowBlur
    property color darkColor: Enums.neumorphism.shadowDark
    property color lightColor: Enums.neumorphism.shadowLight

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _insetActive: inset || pressed
    readonly property real _edgeSize: Math.max(Enums.spacing.xs, blur / 2)

    // ==================== Size 尺寸 ====================
    anchors.fill: target

    // ==================== Content 内容 ====================
    RectangularShadow {
        id: darkShadow
        anchors.fill: parent
        radius: target ? target.radius : 0
        color: root.accent ? Enums.accentColor : root.darkColor
        blur: root.blur
        offset.x: root.inset ? -root.offset : root.offset
        offset.y: root.inset ? -root.offset : root.offset
        spread: root.inset ? -root.offset / 2 : 0
        visible: !root._insetActive
    }

    RectangularShadow {
        id: lightShadow
        anchors.fill: parent
        radius: target ? target.radius : 0
        color: root.lightColor
        blur: root.blur
        offset.x: -root.offset
        offset.y: -root.offset
        spread: 0
        visible: !root._insetActive
    }

    // Concave edge layer is reparented onto the target so it remains visible above an opaque face.
    // 内凹边缘层重定父级到目标表面，避免被不透明底色遮住。
    Item {
        id: insetLayer

        parent: root.target
        anchors.fill: parent
        z: Enums.zIndex.controlsAbove
        clip: true
        visible: root._insetActive

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: root._edgeSize
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0; color: root.darkColor }
                GradientStop { position: 1; color: Enums.transparent }
            }
        }

        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: root._edgeSize
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: root.darkColor }
                GradientStop { position: 1; color: Enums.transparent }
            }
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: root._edgeSize
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0; color: Enums.transparent }
                GradientStop { position: 1; color: root.lightColor }
            }
        }

        Rectangle {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: root._edgeSize
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: Enums.transparent }
                GradientStop { position: 1; color: root.lightColor }
            }
        }
    }
}
