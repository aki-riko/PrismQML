// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// LazyLoadingHelper - Lazy loading logic for StackedWidget 懒加载逻辑辅助器
// Extracted from StackedWidget for modularity 从StackedWidget提取以模块化
Item {
    id: helper
    
    // ==================== Required Props 必需属性 ====================
    required property var loaders           // _loaders array reference
    required property int targetIndex       // Current target index
    required property int currentVisibleIndex // Currently visible page index 当前可见页面索引
    required property var isPageLoadedFunc  // Function to check if page loaded
    required property var isPageLoadFailedFunc // Function to check if page loading failed 检查页面加载是否失败的函数
    required property var pageLoadErrorFunc // Function to obtain the Loader error 获取Loader错误的函数
    required property var activateLoaderFunc // Function to activate loader
    required property var diagnosticFunc // Diagnostic stage callback 诊断阶段回调
    
    // ==================== Public Props 公开属性 ====================
    property string loadingText: { Translator._v; return Translator.tr("loading") }
    property int animationType: Enums.animation.opacity  // Animation type from parent 父级动画类型
    property int animationDuration: Enums.duration.slow  // Animation duration 动画时长
    property int loaderActivationDelay: Enums.duration.none  // Extra delay before Loader activation Loader 激活前额外延迟
    property int popUpOffset: Enums.controlSize.popUpOffset  // PopUp offset PopUp偏移量

    // ==================== Internal Props 内部属性 ====================
    property int pendingTargetIndex: -1
    property bool isLoadingSwitching: false
    property int internalLastIndex: 0
    property int _exitTargetIndex: -1  // Store target index for exit animation callback 存储退出动画回调的目标索引
    property int _observedLoaderIndex: -1
    property int _observedLoaderStatus: Loader.Null
    
    // ==================== Signals 信号 ====================
    signal loadingComplete(int targetIndex, int previousIndex)
    signal loadingFailed(int targetIndex, string errorString)
    signal animationStart()

    function _trace(stage, targetIdx) {
        diagnosticFunc(
            stage,
            targetIdx,
            "helperPending=" + pendingTargetIndex +
            " helperSwitching=" + isLoadingSwitching +
            " observedStatus=" + _observedLoaderStatus)
    }

    function _observeLoaderStatus(targetIdx) {
        var targetLoader = targetIdx >= 0 && targetIdx < loaders.length ?
                    loaders[targetIdx] : null
        var status = targetLoader ? targetLoader.status : Loader.Null
        if (_observedLoaderIndex === targetIdx && _observedLoaderStatus === status) return

        _observedLoaderIndex = targetIdx
        _observedLoaderStatus = status
        _trace("helper.loader_status.changed", targetIdx)
    }

    // ==================== Public Methods 公开方法 ====================
    function cancelPendingLoad() {
        if (pendingTargetIndex >= 0) _trace("helper.cancel_pending.begin", pendingTargetIndex)
        loaderActivateTimer.stop()
        lazyLoadTimer.stop()
        pageRenderTimer.stop()
        pendingTargetIndex = -1
        _observedLoaderIndex = -1
        _observedLoaderStatus = Loader.Null
    }

    function showLoadingAndSwitch(targetIdx) {
        cancelPendingLoad()

        pendingTargetIndex = targetIdx
        isLoadingSwitching = true
        _trace("helper.show.begin", targetIdx)
        _observeLoaderStatus(targetIdx)

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
        loadingOverlay.start()
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
        _trace("helper.show.done", targetIdx)
    }

    function _playExitAnimation(target, targetIdx) {
        _trace("helper.exit_animation.start", targetIdx)
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
        var completedTargetIndex = _exitTargetIndex
        _trace("helper.exit_animation.finish", completedTargetIndex)
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

    function _restoreVisiblePage() {
        var currentLoader = loaders[helper.currentVisibleIndex]
        if (!currentLoader) return

        currentLoader.visible = true
        currentLoader.opacity = 1
        currentLoader.y = 0
        currentLoader.x = 0
        currentLoader.scale = 1
    }

    function _handleLoadFailure(targetIdx, errorString) {
        if (targetIdx !== pendingTargetIndex) return
        _trace("helper.loading_failed.begin", targetIdx)

        loaderActivateTimer.stop()
        lazyLoadTimer.stop()
        pageRenderTimer.stop()

        var failedLoader = loaders[targetIdx]
        if (failedLoader) {
            failedLoader.visible = false
            failedLoader.opacity = 0
            failedLoader.y = 0
            failedLoader.x = 0
            failedLoader.scale = 1
        }
        _restoreVisiblePage()

        loadingOverlay.visible = false
        loadingOverlay.opacity = 0
        loadingOverlay.y = 0
        pendingTargetIndex = -1
        isLoadingSwitching = false
        _exitTargetIndex = -1

        loadingFailed(targetIdx, errorString)
        _trace("helper.loading_failed.done", targetIdx)
    }

    // ==================== Content 内容 ====================
    // Public QML loading page matching SplashScreen 公开的 SplashScreen 同款 QML 加载页
    QMLPage {
        id: loadingOverlay

        objectName: "lazyLoadingOverlay"
        anchors.fill: parent
        text: helper.loadingText
        running: visible && opacity > 0
        visible: false
        opacity: 0
        y: 0
        z: Enums.zIndex.controls

        onFinished: {
            if (helper.pendingTargetIndex < 0) return

            var targetIndex = helper.pendingTargetIndex
            helper._trace("helper.hide_loading.begin", targetIndex)
            loadingOverlay.y = 0
            loadingOverlay.opacity = 1
            helper.pendingTargetIndex = -1
            helper.isLoadingSwitching = false
            helper.animationStart()
            helper._trace("helper.hide_loading.done", targetIndex)
        }
    }

    // Exit animations 退出动画
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
        onFinished: helper._onExitAnimationFinished(target)

        NumberAnimation { target: exitPopUpAnim.target; property: "opacity"; from: 1; to: 0; duration: helper.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { target: exitPopUpAnim.target; property: "y"; from: 0; to: helper.popUpOffset; duration: helper.animationDuration; easing.type: Easing.OutCubic }
    }
    
    // PopDown exit (fade + move up) PopDown退出（淡出+上移）
    ParallelAnimation {
        id: exitPopDownAnim
        property Item target
        onFinished: helper._onExitAnimationFinished(target)

        NumberAnimation { target: exitPopDownAnim.target; property: "opacity"; from: 1; to: 0; duration: helper.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { target: exitPopDownAnim.target; property: "y"; from: 0; to: -helper.popUpOffset; duration: helper.animationDuration; easing.type: Easing.OutCubic }
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
    
    // Timers 定时器
    Timer {
        id: loaderActivateTimer
        objectName: "lazyLoaderActivateTimer"
        property int targetIndex: 0
        interval: Math.max(
            Enums.duration.tick,
            helper.loaderActivationDelay - helper.animationDuration
        )  // Keep indicator feedback ahead of loading 让指示器反馈先于加载
        onTriggered: {
            if (targetIndex !== helper.pendingTargetIndex) return

            helper._trace("helper.loader_activate.begin", targetIndex)
            helper.activateLoaderFunc(targetIndex)
            helper._observeLoaderStatus(targetIndex)
            helper._trace("helper.loader_activate.done", targetIndex)
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

            helper._observeLoaderStatus(targetIndex)
            if (helper.isPageLoadedFunc(targetIndex)) {
                stop()
                helper._trace("helper.page_ready", targetIndex)
                pageRenderTimer.targetIndex = targetIndex
                pageRenderTimer.start()
                return
            }

            if (helper.isPageLoadFailedFunc(targetIndex)) {
                stop()
                helper._handleLoadFailure(
                    targetIndex, helper.pageLoadErrorFunc(targetIndex))
            }
        }
    }
    
    Timer {
        id: pageRenderTimer
        property int targetIndex: 0
        interval: Enums.duration.ultraFast  // Wait for render stable 等待渲染稳定
        onTriggered: {
            if (targetIndex !== helper.pendingTargetIndex) return

            helper._trace("helper.page_render.begin", targetIndex)
            var prevIdx = helper.internalLastIndex
            helper.internalLastIndex = targetIndex
            helper._trace("helper.loading_complete.emit_begin", targetIndex)
            helper.loadingComplete(targetIndex, prevIdx)
            helper._trace("helper.loading_complete.emit_done", targetIndex)
            loadingOverlay.finish()
            helper._trace("helper.page_render.done", targetIndex)
        }
    }
}
