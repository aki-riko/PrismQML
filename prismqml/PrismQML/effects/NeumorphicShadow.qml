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
    readonly property point _targetPosition: _mapTargetPosition()

    // ==================== Internal Methods 内部方法 ====================
    function _mapTargetPosition() {
        if (!target || !root.parent) return Qt.point(0, 0)

        // Touch every visual ancestor geometry so the binding is reevaluated when a
        // nested target moves with one of its containers. 读取每层可视祖先的
        // 几何属性，使嵌套容器移动时坐标映射能够同步更新。
        var geometryDependency = 0
        var current = target
        while (current && current !== root.parent) {
            geometryDependency += current.x + current.y + current.width + current.height
            geometryDependency += current.scale + current.rotation + current.transformOrigin
            current = current.parent
        }
        if (!isFinite(geometryDependency)) return Qt.point(0, 0)
        return target.mapToItem(root.parent, 0, 0)
    }

    // ==================== Size 尺寸 ====================
    x: _targetPosition.x
    y: _targetPosition.y
    width: target ? target.width : 0
    height: target ? target.height : 0

    // ==================== Content 内容 ====================
    Loader {
        id: outerShadowLoader

        objectName: "_neumorphicOuterShadowLoader"
        anchors.fill: parent
        active: root.visible && !root._insetActive && root.target !== null
        sourceComponent: Component {
            Item {
                anchors.fill: parent

                RectangularShadow {
                    objectName: "_neumorphicDarkOuterShadow"
                    anchors.fill: parent
                    radius: root.target && root.target.radius !== undefined
                            ? root.target.radius : 0
                    color: root.accent ? Enums.accentColor : root.darkColor
                    blur: root.blur
                    offset.x: root.offset
                    offset.y: root.offset
                    spread: 0
                }

                RectangularShadow {
                    objectName: "_neumorphicLightOuterShadow"
                    anchors.fill: parent
                    radius: root.target && root.target.radius !== undefined
                            ? root.target.radius : 0
                    color: root.lightColor
                    blur: root.blur
                    offset.x: -root.offset
                    offset.y: -root.offset
                    spread: 0
                }
            }
        }
    }

    // Concave edge layer is reparented onto the target so it remains visible above an opaque face.
    // 内凹边缘层重定父级到目标表面，避免被不透明底色遮住。
    Loader {
        id: insetLayerLoader

        objectName: "_neumorphicInsetLayerLoader"
        active: root.visible && root._insetActive && root.target !== null
        sourceComponent: Component {
            Item {
                objectName: "_neumorphicInsetLayer"
                parent: root.target
                anchors.fill: parent
                z: Enums.zIndex.controlsAbove
                clip: true

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
    }
}
