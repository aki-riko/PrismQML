// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."

// Skeleton - 骨架屏 Skeleton loading placeholder
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property bool loading: true
    property int shape: Enums.skeleton.shape_rounded  // shape_rect / shape_circle / shape_rounded
    
    // ==================== Internal Props 内部属性 ====================
    // Viewport detection lives in ViewportMixin 视口检测由 ViewportMixin 持有
    readonly property bool _isInViewport: viewport.isInViewport

    // ==================== Readonly State 只读状态 ====================
    readonly property color baseColor: Enums.stateColor.skeletonBase
    readonly property color shimmerColor: Enums.stateColor.skeletonShimmer

    readonly property real _radius: {
        switch (control.shape) {
            case Enums.skeleton.shape_rect: return Enums.radius.small// 方形也需要圆角
            case Enums.skeleton.shape_circle: return Math.min(width, height) / 2
            default: return Enums.radius.small
        }
    }
    
    // ==================== Public Methods 公开方法 ====================
    // Start loading 开始加载
    function start() {
        loading = true
    }

    // Stop loading 停止加载
    function stop() {
        loading = false
    }

    // Set animated (always true in this impl) 设置动画启用
    function setAnimated(a) { /* Always animated */ }
    
    // ==================== Size 尺寸 ====================
    implicitWidth: shape === Enums.skeleton.shape_circle ? Enums.skeletonMetrics.circleSize : Enums.skeletonMetrics.rectWidth
    implicitHeight: shape === Enums.skeleton.shape_circle ? Enums.skeletonMetrics.circleSize : Enums.skeletonMetrics.rectHeight
    visible: loading

    // ==================== Content 内容 ====================
    ViewportMixin {
        id: viewport
        target: control
    }

    // Content container 内容容器
    Item {
        id: contentContainer
        anchors.fill: parent

        // Apply mask 应用遮罩 (只在可视时启用 layer 减少 GPU 开销)
        layer.enabled: control._isInViewport
        layer.effect: MultiEffect {
            maskEnabled: true
            maskSource: maskShape
            maskThresholdMin: 0.5
            maskSpreadAtMin: 0.0
        }

        // ==================== Content 内容 ====================
        
        // Background 背景
        Rectangle {
            id: background
            anchors.fill: parent
            radius: control._radius
            color: control.baseColor
        }
        
        // Shimmer effect 闪光效果
        Rectangle {
            id: shimmer
            objectName: "skeletonShimmer"
            width: parent.width * Enums.skeletonMetrics.shimmerWidthRatio
            height: parent.height
            x: -width
            
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: Enums.isVintageTicket ? control.baseColor : Enums.transparent }
                GradientStop { position: 0.5; color: control.shimmerColor }
                GradientStop { position: 1; color: Enums.isVintageTicket ? control.baseColor : Enums.transparent }
            }
            
            SequentialAnimation on x {
                running: control.loading && control.visible && control._isInViewport
                loops: Animation.Infinite
                
                NumberAnimation { 
                    from: -shimmer.width
                    to: contentContainer.width
                    duration: Enums.skeletonMetrics.shimmerDurationMs
                    easing.type: Easing.InOutQuad
                }
                PauseAnimation { duration: Enums.skeletonMetrics.shimmerPauseMs }
            }
        }
    }
    
    // Mask shape 遮罩形状
    Rectangle {
        id: maskShape
        anchors.fill: parent
        radius: control._radius
        color: Enums.textColor.primary
        visible: false
        layer.enabled: control._isInViewport
    }
}
