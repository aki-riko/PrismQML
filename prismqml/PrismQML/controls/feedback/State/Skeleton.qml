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
            case Enums.skeleton.shape_rect: return Enums.radius.small// Square blocks still need rounded corners 方形也需要圆角
            case Enums.skeleton.shape_circle: return Math.min(width, height) / 2
            default: return Enums.radius.small
        }
    }
    // The mask is what makes the shimmer follow the outline, but it also forces every
    // placeholder through an offscreen layer and a MultiEffect pass. A rounded
    // rectangle's background already carries its own radius, so only a circular
    // placeholder needs the mask: without it the shimmer would show square corners
    // against the circle.
    // 遮罩让闪烁沿轮廓走, 但它也会把每个占位块送进离屏图层与 MultiEffect 通道。圆角矩形
    // 的背景本身已带圆角, 因此只有圆形占位块需要遮罩: 否则闪烁会在圆形上露出方角。
    readonly property bool _needsMask:
        control.shape === Enums.skeleton.shape_circle
    
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

        // Apply mask 应用遮罩 (只在可视且需要轮廓裁剪时启用 layer 减少 GPU 开销)
        layer.enabled: control._isInViewport && control._needsMask
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
        layer.enabled: control._isInViewport && control._needsMask
    }
}
