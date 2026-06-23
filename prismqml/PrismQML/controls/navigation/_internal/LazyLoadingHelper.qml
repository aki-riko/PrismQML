// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../feedback"
import "../../data"

// LazyLoadingHelper - Lazy loading logic for StackedWidget 懒加载逻辑辅助器
// Extracted from StackedWidget for modularity 从StackedWidget提取以模块化
Item {
    id: helper
    
    // ==================== Required Props 必需属性 ====================
    required property var loaders           // _loaders array reference
    required property int targetIndex       // Current target index
    required property int currentVisibleIndex // Currently visible page index 当前可见页面索引
    required property var isPageLoadedFunc  // Function to check if page loaded
    required property var activateLoaderFunc // Function to activate loader
    
    // ==================== Props 属性 ====================
    property string loadingText: Translator.tr("loading")
    property int animationType: Enums.animation.opacity  // Animation type from parent 父级动画类型
    property int animationDuration: Enums.duration.slow  // Animation duration 动画时长
    property int popUpOffset: Enums.controlSize.popUpOffset  // PopUp offset PopUp偏移量
    property int pendingTargetIndex: -1
    property bool isLoadingSwitching: false
    property int internalLastIndex: 0
    
    // ==================== Signals 信号 ====================
    signal loadingComplete(int targetIndex, int previousIndex)
    signal animationStart()

    property int _exitTargetIndex: -1  // Store target index for exit animation callback 存储退出动画回调的目标索引

    // ==================== Public Methods 公开方法 ====================
    function cancelPendingLoad() {
        loaderActivateTimer.stop()
        lazyLoadTimer.stop()
        pageRenderTimer.stop()
        hideLoadingTimer.stop()
        pendingTargetIndex = -1
    }

    function showLoadingAndSwitch(targetIdx) {
        cancelPendingLoad()

        pendingTargetIndex = targetIdx
        isLoadingSwitching = true

        // Hide other pages immediately (except current visible) 立即隐藏其他页面（当前可见页面除外）
        for (var i = 0; i < loaders.length; i++) {
            if (loaders[i] && i !== helper.currentVisibleIndex) {
                loaders[i].visible = false
                loaders[i].opacity = 0
                loaders[i].y = 0
                loaders[i].x = 0
                loaders[i].scale = 1
            }
        }

        // Show loading overlay 显示加载页
        loadingOverlay.visible = true
        loadingOverlay.y = 0
        loadingOverlay.opacity = 1

        // Phase 1: Play exit animation for old page based on animationType 第一阶段：根据动画类型播放旧页面退出动画
        // Loader activation will start after exit animation finishes Loader激活将在退出动画完成后开始
        var currentLoader = loaders[helper.currentVisibleIndex]
        if (currentLoader && currentLoader.visible) {
            _playExitAnimation(currentLoader, targetIdx)
        } else {
            // No old page to animate, start loader activation immediately 没有旧页面需要动画，立即开始激活Loader
            loaderActivateTimer.targetIndex = targetIdx
            loaderActivateTimer.start()
        }
    }

    function _playExitAnimation(target, targetIdx) {
        // Store target index for callback 存储目标索引用于回调
        _exitTargetIndex = targetIdx

        // Reset all animation targets 重置所有动画目标
        exitFadeAnim.stop()
        exitPopUpAnim.stop()
        exitPopDownAnim.stop()
        exitZoomAnim.stop()
        exitSlideAnim.stop()

        switch (animationType) {
            case Enums.animation.opacity:
                exitFadeAnim.target = target
                exitFadeAnim.start()
                break
            case Enums.animation.popup:
                exitPopUpAnim.target = target
                exitPopUpAnim.start()
                break
            case Enums.animation.popdown:
                exitPopDownAnim.target = target
                exitPopDownAnim.start()
                break
            case Enums.animation.zoom:
                exitZoomAnim.target = target
                exitZoomAnim.start()
                break
            case Enums.animation.slide:
            case Enums.animation.card:
                exitSlideAnim.target = target
                exitSlideAnim.to = -helper.width
                exitSlideAnim.start()
                break
            default:
                exitFadeAnim.target = target
                exitFadeAnim.start()
        }
    }

    function _onExitAnimationFinished(target) {
        if (target) {
            target.visible = false
            target.opacity = 1
            target.y = 0
            target.x = 0
            target.scale = 1
        }

        // Start loader activation after exit animation completes 退出动画完成后开始激活 Loader

        if (_exitTargetIndex >= 0 && _exitTargetIndex === pendingTargetIndex) {
            loaderActivateTimer.targetIndex = _exitTargetIndex
            loaderActivateTimer.start()
        }
        _exitTargetIndex = -1
    }

    // ==================== Loading Overlay 加载覆盖层 ====================
    // Custom loading overlay with render thread animation, using RotationAnimator to avoid freeze during Loader instantiation. 自定义加载覆盖层（渲染线程动画），使用 RotationAnimator 避免 Loader 实例化时卡顿。
    Item {
        id: loadingOverlay
        anchors.fill: parent
        visible: false
        opacity: 0
        y: 0
        z: Enums.zIndex.controls
        
        property alias text: loadingText.text
        property bool running: visible && opacity > 0
        
        Rectangle {
            anchors.fill: parent
            color: "transparent"  // Transparent to let parent bg show through 透明以显示父级背景
        }
        
        Column {
            anchors.centerIn: parent
            spacing: Enums.spacing.xl
            
            // Render thread progress ring 渲染线程进度环
            Item {
                id: ringContainer
                width: Enums.controlSize.navBarHeight
                height: Enums.controlSize.navBarHeight
                anchors.horizontalCenter: parent.horizontalCenter
                
                RotationAnimator on rotation {
                    from: 0
                    to: 360
                    duration: Enums.duration.scroll
                    loops: Animation.Infinite
                    running: loadingOverlay.running
                }
                
                Canvas {
                    id: ringCanvas
                    anchors.fill: parent
                    
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        
                        var centerX = width / 2
                        var centerY = height / 2
                        var strokeWidth = Enums.controlSize.progressStrokeWidth
                        var radius = Math.min(centerX, centerY) - strokeWidth / 2
                        
                        ctx.strokeStyle = Enums.accentColor
                        ctx.lineWidth = strokeWidth
                        ctx.lineCap = "round"
                        
                        var startRad = -Math.PI / 2
                        var endRad = startRad + Math.PI / 2
                        
                        ctx.beginPath()
                        ctx.arc(centerX, centerY, radius, startRad, endRad, false)
                        ctx.stroke()
                    }
                    
                    Component.onCompleted: requestPaint()
                }
            }
            
            // Loading text 加载文字
            Label {
                id: loadingText
                type: Enums.label.type_body
                text: helper.loadingText
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
        
        Behavior on y {
            enabled: !helper.isLoadingSwitching  // Disable during instant show 立即显示时禁用
            NumberAnimation {
                duration: Enums.duration.medium
                easing.type: Easing.OutCubic
            }
        }
        
        Behavior on opacity {
            enabled: !helper.isLoadingSwitching  // Disable during instant show 立即显示时禁用
            NumberAnimation {
                duration: Enums.duration.medium
                easing.type: Easing.OutCubic
            }
        }
    }

    // ==================== Exit Animations 退出动画 ====================
    // Fade exit 淡出

    NumberAnimation {
        id: exitFadeAnim
        property: "opacity"
        from: 1; to: 0
        duration: helper.animationDuration
        easing.type: Easing.OutCubic
        onFinished: helper._onExitAnimationFinished(target)
    }
    
    // PopUp exit (fade + move down) PopUp退出（淡出+下移）
    ParallelAnimation {
        id: exitPopUpAnim
        property Item target
        NumberAnimation { target: exitPopUpAnim.target; property: "opacity"; from: 1; to: 0; duration: helper.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { target: exitPopUpAnim.target; property: "y"; from: 0; to: helper.popUpOffset; duration: helper.animationDuration; easing.type: Easing.OutCubic }
        onFinished: helper._onExitAnimationFinished(target)
    }
    
    // PopDown exit (fade + move up) PopDown退出（淡出+上移）
    ParallelAnimation {
        id: exitPopDownAnim
        property Item target
        NumberAnimation { target: exitPopDownAnim.target; property: "opacity"; from: 1; to: 0; duration: helper.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { target: exitPopDownAnim.target; property: "y"; from: 0; to: -helper.popUpOffset; duration: helper.animationDuration; easing.type: Easing.OutCubic }
        onFinished: helper._onExitAnimationFinished(target)
    }
    
    // Zoom exit 缩放退出
    NumberAnimation {
        id: exitZoomAnim
        property: "scale"
        from: 1; to: 0
        duration: helper.animationDuration / 2
        easing.type: Easing.InQuad
        onFinished: helper._onExitAnimationFinished(target)
    }
    
    // Slide exit 滑动退出
    NumberAnimation {
        id: exitSlideAnim
        property: "x"
        from: 0
        duration: helper.animationDuration
        easing.type: Easing.OutCubic
        onFinished: helper._onExitAnimationFinished(target)
    }
    
    // ==================== Timers 定时器 ====================
    Timer {
        id: loaderActivateTimer
        property int targetIndex: 0
        interval: Enums.duration.tick  // High-refresh tick 高刷定时器
        onTriggered: {
            if (targetIndex !== helper.pendingTargetIndex) return
            
            helper.activateLoaderFunc(targetIndex)
            lazyLoadTimer.targetIndex = targetIndex
            lazyLoadTimer.start()
        }
    }
    
    Timer {
        id: lazyLoadTimer
        property int targetIndex: 0
        interval: Enums.duration.tick  // High-refresh tick 高刷定时器
        repeat: true
        onTriggered: {
            if (targetIndex !== helper.pendingTargetIndex) {
                stop()
                return
            }
            
            if (helper.isPageLoadedFunc(targetIndex)) {
                stop()
                pageRenderTimer.targetIndex = targetIndex
                pageRenderTimer.start()
            }
        }
    }
    
    Timer {
        id: pageRenderTimer
        property int targetIndex: 0
        interval: Enums.duration.ultraFast  // Wait for render stable 等待渲染稳定
        onTriggered: {
            if (targetIndex !== helper.pendingTargetIndex) return
            
            loadingOverlay.y = Enums.controlSize.popUpOffset
            loadingOverlay.opacity = 0
            hideLoadingTimer.targetIndex = targetIndex
            hideLoadingTimer.start()
        }
    }
    
    Timer {
        id: hideLoadingTimer
        property int targetIndex: 0
        interval: Enums.duration.ultraFast  // Hide loading overlay 隐藏加载动画
        onTriggered: {
            if (targetIndex !== helper.pendingTargetIndex) return
            
            loadingOverlay.visible = false
            loadingOverlay.y = 0
            
            var prevIdx = helper.internalLastIndex
            helper.internalLastIndex = targetIndex
            helper.pendingTargetIndex = -1
            helper.isLoadingSwitching = false
            
            helper.loadingComplete(targetIndex, prevIdx)
            helper.animationStart()
        }
    }
}
