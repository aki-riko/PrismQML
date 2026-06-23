// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."

// Skeleton - 骨架屏 Skeleton loading placeholder
Item {
    id: control
    
    // ==================== Props 属性 ====================
    property bool loading: true
    property int shape: Enums.skeleton.shape_rounded  // shape_rect / shape_circle / shape_rounded
    
    // ==================== Viewport Detection 可视区域检测 ====================
    property Item _flickableAncestor: null
    property bool _isInViewport: true  // 默认可见，找不到 Flickable 时保持动画
    
    // Find Flickable ancestor upwards 向上查找 Flickable 祖先
    function _findFlickable() {
        var p = control.parent
        while (p) {
            if (p instanceof Flickable) return p
            p = p.parent
        }
        return null
    }
    
    // Calculate if in viewport 计算是否在可视区域
    function _updateViewport() {
        try {
            if (!_flickableAncestor || !control.visible) {
                _isInViewport = control.visible
                return
            }
            // Check if contentItem exists 检查contentItem是否存在
            if (!_flickableAncestor.contentItem) {
                _isInViewport = true
                return
            }
            // Check if height is valid 检查高度是否有效
            if (_flickableAncestor.height <= 0) {
                _isInViewport = true
                return
            }
            var pos = control.mapToItem(_flickableAncestor.contentItem, 0, 0)
            var viewTop = _flickableAncestor.contentY
            var viewBottom = viewTop + _flickableAncestor.height
            // Add buffer to avoid edge flicker 加一点缓冲区避免边缘闪烁
            var buffer = control.height
            _isInViewport = (pos.y + control.height + buffer > viewTop) && (pos.y - buffer < viewBottom)
        } catch (e) {
            // Fallback to visible if any error occurs 发生任何错误时回退到可见
            _isInViewport = true
        }
    }
    
    Component.onCompleted: {
        _flickableAncestor = _findFlickable()
        if (_flickableAncestor) {
            _flickableAncestor.contentYChanged.connect(_updateViewport)
            _flickableAncestor.heightChanged.connect(_updateViewport)
        }
        _updateViewport()
    }
    
    onVisibleChanged: _updateViewport()
    onYChanged: if (_flickableAncestor) Qt.callLater(_updateViewport)
    
    // ==================== Colors 颜色 ====================
    readonly property color baseColor: Enums.stateColor.skeletonBase
    readonly property color shimmerColor: Enums.stateColor.skeletonShimmer
    
    // ==================== Computed radius 计算圆角 ====================
    readonly property real _radius: {
        switch (control.shape) {
            case Enums.skeleton.shape_rect: return Enums.radius.small  // 方形也需要圆角
            case Enums.skeleton.shape_circle: return Math.min(width, height) / 2
            default: return Enums.radius.small
        }
    }
    
    // ==================== Size 尺寸 ====================
    implicitWidth: shape === Enums.skeleton.shape_circle ? Enums.skeletonMetrics.circleSize : Enums.skeletonMetrics.rectWidth
    implicitHeight: shape === Enums.skeleton.shape_circle ? Enums.skeletonMetrics.circleSize : Enums.skeletonMetrics.rectHeight
    visible: loading

    // ==================== Public Methods 公共方法 ====================
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

    // ==================== Content Container 内容容器 ====================
    Item {
        id: contentContainer
        anchors.fill: parent
        
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
            width: parent.width * Enums.skeletonMetrics.shimmerWidthRatio
            height: parent.height
            x: -width
            
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: Enums.transparent }
                GradientStop { position: 0.5; color: control.shimmerColor }
                GradientStop { position: 1; color: Enums.transparent }
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
        
        // Apply mask 应用遮罩 (只在可视时启用 layer 减少 GPU 开销)
        layer.enabled: control._isInViewport
        layer.effect: MultiEffect {
            maskEnabled: true
            maskSource: maskShape
            maskThresholdMin: 0.5
            maskSpreadAtMin: 0.0
        }
    }
    
    // ==================== Mask Shape 遮罩形状 ====================
    Rectangle {
        id: maskShape
        anchors.fill: parent
        radius: control._radius
        color: Enums.textColor.primary
        visible: false
        layer.enabled: true
    }
}
