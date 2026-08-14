// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import ".."

// NeumorphicShadow - paired soft light/dark shadows 新拟态双向软阴影
// One reusable primitive provides convex and concave surfaces for all controls.
// 统一提供凸起与凹入表面，避免控件散落手写阴影。
Loader {
    id: root

    // ==================== Public Props 公开属性 ====================
    property Item target: parent
    property bool inset: false
    property bool pressed: false
    property bool accent: false
    property real offset: Enums.neumorphism.shadowOffset
    property real blur: Enums.neumorphism.shadowBlur
    property real spread: Enums.neumorphism.shadowSpread
    property color darkColor: Enums.neumorphism.shadowDark
    property color lightColor: Enums.neumorphism.shadowLight
    property real insetDarkOpacity: Enums.neumorphism.insetDarkOpacity
    property real insetLightOpacity: Enums.neumorphism.insetLightOpacity

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _insetActive: inset || pressed
    readonly property real _edgeSize: Math.max(
        Enums.spacing.xxs,
        Math.min(Enums.neumorphism.insetEdgeSize, offset)
    )
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
    active: visible && target !== null
    source: active
            ? Qt.resolvedUrl(_insetActive
                             ? "_internal/NeumorphicInsetLayer.qml"
                             : "_internal/NeumorphicOuterShadow.qml")
            : ""
}
