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
    required property var isPageLoadedFunc  // Function to check if page loaded 检查页面是否已加载的函数
    required property var isPageLoadFailedFunc // Function to check if page loading failed 检查页面加载是否失败的函数
    required property var pageLoadErrorFunc // Function to obtain the Loader error 获取Loader错误的函数
    required property var activateLoaderFunc // Function to activate loader 激活加载器的函数
    required property var diagnosticFunc // Diagnostic stage callback 诊断阶段回调
    required property var pageTransition // Shared page-circle transition 共享页面圆形过渡
    
    // ==================== Public Props 公开属性 ====================
    property string loadingText: { Translator._v; return Translator.tr("loading") }
    property int loadingAnimationType: Enums.animation.opacity
    property int loadingAnimationDuration: Enums.duration.medium
    property int loaderActivationDelay: Enums.duration.none  // Extra delay before Loader activation Loader 激活前额外延迟

    // ==================== Internal Props 内部属性 ====================
    property int pendingTargetIndex: -1
    property bool isLoadingSwitching: false
    property int internalLastIndex: 0
    property int _observedLoaderIndex: -1
    property int _observedLoaderStatus: Loader.Null
    property bool _waitIndicatorFinished: false
    property bool _targetExpansionFinished: false
    property bool _initialLoading: false
    property int _deferredRevealTarget: -1
    
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

    function _stopStageTimer() {
        stageTimer.stop()
        stageTimer._activationPhase = false
        stageTimer._renderPhase = false
    }

    function _startLoaderActivationTimer(targetIdx) {
        stageTimer.stop()
        stageTimer.targetIndex = targetIdx
        stageTimer._activationPhase = true
        stageTimer._renderPhase = false
        stageTimer.start()
    }

    function _startLoaderPollingTimer(targetIdx) {
        stageTimer.stop()
        stageTimer.targetIndex = targetIdx
        stageTimer._activationPhase = false
        stageTimer._renderPhase = false
        stageTimer.start()
    }

    function _startPageRenderTimer(targetIdx) {
        stageTimer.stop()
        stageTimer.targetIndex = targetIdx
        stageTimer._activationPhase = false
        stageTimer._renderPhase = true
        stageTimer.start()
    }

    function _activateLoaderAndStartPolling(targetIdx) {
        if (targetIdx !== pendingTargetIndex) return

        _trace("helper.loader_activate.begin", targetIdx)
        activateLoaderFunc(targetIdx)
        _observeLoaderStatus(targetIdx)
        _trace("helper.loader_activate.done", targetIdx)
        _startLoaderPollingTimer(targetIdx)
    }

    function _pollLoader(targetIdx) {
        if (targetIdx !== pendingTargetIndex) {
            _rearmDroppedPhase()
            return
        }

        _observeLoaderStatus(targetIdx)
        if (isPageLoadedFunc(targetIdx)) {
            _trace("helper.page_ready", targetIdx)
            _startPageRenderTimer(targetIdx)
            return
        }

        if (isPageLoadFailedFunc(targetIdx)) {
            _handleLoadFailure(targetIdx, pageLoadErrorFunc(targetIdx))
        }
    }

    function _rearmDroppedPhase() {
        // A retarget that lands between arming a phase callback and its timeout
        // must not drop the switch. The render phase timer is single-shot, so
        // returning here leaves no owner for the loading overlay exit and the
        // overlay (spinner + caption) stays on screen forever. Re-arm the phase
        // for the index that is actually pending. A cancelled switch keeps its
        // old behaviour: isLoadingSwitching is false there, so the timer stops.
        // 目标索引在阶段回调武装与触发之间变化时不得丢弃整次切换。渲染阶段计时器是
        // 单次的, 就此 return 会让遮罩退场失去持有者, 遮罩(转圈+文案)会永久留在
        // 屏幕上。此处为真正待处理的索引重新武装对应阶段。已取消的切换保持原行为:
        // 那种情况 isLoadingSwitching 为 false, 计时器停止。
        var pending = pendingTargetIndex
        if (!isLoadingSwitching || pending < 0) {
            _trace("helper.dropped_phase.stop", pending)
            _stopStageTimer()
            // A dropped phase whose switch is already cancelled keeps no owner
            // for the overlay exit, so release a still-visible overlay here.
            // The normal exit path is untouched: the overlay is already hidden
            // by then and this only reads it.
            // 已取消的切换丢弃阶段后没有任何持有者负责遮罩退场, 因此在此释放仍然
            // 可见的遮罩。正常退场路径不受影响: 那时遮罩已隐藏, 此处只做读取。
            _releaseOverlayIfVisible()
            return
        }
        _trace("helper.dropped_phase.rearm", pending)
        if (isPageLoadFailedFunc(pending)) {
            _handleLoadFailure(pending, pageLoadErrorFunc(pending))
            return
        }
        if (isPageLoadedFunc(pending)) {
            _startPageRenderTimer(pending)
            return
        }
        _startLoaderPollingTimer(pending)
    }

    function _completePageRender(targetIdx) {
        if (targetIdx !== pendingTargetIndex) {
            _rearmDroppedPhase()
            return
        }

        if (_initialLoading) {
            _initialLoading = false
            _targetExpansionFinished = true
            _finishLoadingOverlay()
            return
        }

        _trace("helper.page_render.begin", targetIdx)
        var prevIdx = internalLastIndex
        if (helper.pageTransition.animationType === Enums.lazyAnimation.none) {
            _deferredRevealTarget = targetIdx
            _trace("helper.page_render.defer_until_wait_exit", targetIdx)
            pageTransition.expand(loaders[targetIdx])
            return
        }
        internalLastIndex = targetIdx
        _trace("helper.loading_complete.emit_begin", targetIdx)
        loadingComplete(targetIdx, prevIdx)
        _trace("helper.loading_complete.emit_done", targetIdx)
        var targetLoader = loaders[targetIdx]
        pageTransition.expand(targetLoader)
        _trace("helper.page_render.done", targetIdx)
    }

    function _beginTargetExpansion() {
        if (pendingTargetIndex < 0) {
            // The switch was cancelled while the overlay was on screen; nothing
            // else owns its exit, so release it instead of leaving it forever.
            // 遮罩仍在屏上时切换被取消, 没有其他持有者负责退场, 故在此释放,
            // 而不是让它永久停留。
            _releaseOverlayIfVisible()
            return
        }

        _trace("helper.page_expand.begin", pendingTargetIndex)
        if (!loadingOverlay.visible) {
            _waitIndicatorFinished = true
            _finalizeLoadingSwitch()
            return
        }
        _finishLoadingOverlay()
    }

    function _releaseOverlayIfVisible() {
        // Exit the wait indicator when it is still on screen. QMLPage.finish()
        // runs the shared fade/shrink exit and then emits finished, so this
        // reuses the existing normal exit rather than hiding the overlay
        // abruptly. Do not loop: a hidden overlay must never restart the exit.
        // 等待指示仍在屏上时执行退场。QMLPage.finish() 走既有的淡出/缩小退场并在
        // 结束后发出 finished, 因此这里复用正常退场而不是生硬隐藏。不循环:
        // 已隐藏时绝不重启退场。
        if (!loadingOverlay.visible || loadingOverlay.finishing) return
        _trace("helper.overlay.release_without_owner", pendingTargetIndex)
        _finishLoadingOverlay()
    }

    function _completeWaitIndicatorExit() {
        if (pendingTargetIndex < 0) {
            // The exit landed after the switch lost its pending target and the
            // overlay is somehow still visible: release it once more so no path
            // can leave the spinner and caption parked on screen.
            // 退场回调到达时切换已失去待处理目标, 而遮罩仍可见: 再释放一次,
            // 保证任何路径都不会把转圈与文案永久留在屏幕上。
            _releaseOverlayIfVisible()
            return
        }

        _waitIndicatorFinished = true
        _trace("helper.wait_indicator.finish", pendingTargetIndex)
        if (_deferredRevealTarget >= 0) {
            var revealTarget = _deferredRevealTarget
            _deferredRevealTarget = -1
            _trace("helper.page_reveal.after_wait", revealTarget)
            var prevIdx = internalLastIndex
            internalLastIndex = revealTarget
            loadingComplete(revealTarget, prevIdx)
        }
        _finalizeLoadingSwitch()
    }

    function _finalizeLoadingSwitch() {
        if (pendingTargetIndex < 0 || !_waitIndicatorFinished
                || !_targetExpansionFinished) return

        var targetIndex = pendingTargetIndex
        _trace("helper.hide_loading.begin", targetIndex)
        loadingOverlay.y = 0
        loadingOverlay.opacity = 1
        pendingTargetIndex = -1
        isLoadingSwitching = false
        _waitIndicatorFinished = false
        _targetExpansionFinished = false
        animationStart()
        _trace("helper.hide_loading.done", targetIndex)
    }

    // ==================== Public Methods 公开方法 ====================
    function cancelPendingLoad() {
        var cancelledTargetIndex = pendingTargetIndex
        if (cancelledTargetIndex >= 0) {
            _trace("helper.cancel_pending.begin", cancelledTargetIndex)
        }
        _stopStageTimer()
        pageTransition.stop()
        if (cancelledTargetIndex >= 0) _restoreVisiblePage()
        pendingTargetIndex = -1
        isLoadingSwitching = false
        _observedLoaderIndex = -1
        _observedLoaderStatus = Loader.Null
        _waitIndicatorFinished = false
        _targetExpansionFinished = false
        _initialLoading = false
        _deferredRevealTarget = -1
        loadingOverlayEnterAnimation.stop()
        loadingOverlay.visible = false
        loadingOverlay.opacity = 0
        loadingOverlay.y = 0
        _trace("helper.cancel_pending.done", cancelledTargetIndex)
    }

    function showLoadingAndSwitch(targetIdx) {
        cancelPendingLoad()

        pendingTargetIndex = targetIdx
        isLoadingSwitching = true
        _waitIndicatorFinished = false
        _targetExpansionFinished = false
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

        var currentLoader = loaders[helper.currentVisibleIndex]
        pageTransition.collapse(currentLoader)
        _trace("helper.show.done", targetIdx)
    }

    function showInitialLoading(targetIdx) {
        cancelPendingLoad()
        pendingTargetIndex = targetIdx
        isLoadingSwitching = true
        _initialLoading = true
        _waitIndicatorFinished = false
        _targetExpansionFinished = false
        _startLoadingOverlay()
        _trace("helper.initial_loading.start", targetIdx)
        _startLoaderPollingTimer(targetIdx)
    }

    function _completeLoadingCollapse() {
        var targetIdx = pendingTargetIndex
        if (targetIdx < 0) return

        _trace("helper.page_collapse.finish", targetIdx)
        _startLoadingOverlay()
        _trace("helper.wait_indicator.start", targetIdx)
        _startLoaderActivationTimer(targetIdx)
    }

    function _completeTargetExpansion() {
        if (pendingTargetIndex < 0) return

        _trace("helper.page_expand.finish", pendingTargetIndex)
        _targetExpansionFinished = true
        _finalizeLoadingSwitch()
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

    function _finishLoadingOverlay() {
        // Stop the enter animation before starting the exit animation. Otherwise
        // both animations write opacity/scale and the spinner can reappear after
        // the page has already finished expanding.
        // 启动退场动画前先停止入场动画。否则两个动画同时写 opacity/scale，
        // 页面已经展开后，转圈覆盖层仍可能被入场动画写回可见。
        loadingOverlayEnterAnimation.stop()
        loadingOverlay.finish()
    }

    function _startLoadingOverlay() {
        loadingOverlay.start()
        loadingOverlay.x = 0
        loadingOverlay.y = 0
        loadingOverlay.scale = 1
        loadingOverlay.opacity = 0
        switch (loadingAnimationType) {
        case Enums.animation.slide:
        case Enums.animation.slide_fade:
            loadingOverlay.x = width
            break
        case Enums.animation.popup:
            loadingOverlay.y = Enums.controlSize.popUpOffset
            break
        case Enums.animation.popdown:
            loadingOverlay.y = -Enums.controlSize.popUpOffset
            break
        case Enums.animation.zoom:
            loadingOverlay.scale = Enums.opacityLevel.invisible
            break
        }
        loadingOverlayEnterAnimation.restart()
    }

    function _handleLoadFailure(targetIdx, errorString) {
        if (targetIdx !== pendingTargetIndex) return
        _trace("helper.loading_failed.begin", targetIdx)

        _stopStageTimer()
        pageTransition.stop()

        var failedLoader = loaders[targetIdx]
        if (failedLoader) {
            failedLoader.visible = false
            failedLoader.opacity = 0
            failedLoader.y = 0
            failedLoader.x = 0
            failedLoader.scale = 1
        }
        _restoreVisiblePage()

        loadingOverlayEnterAnimation.stop()
        loadingOverlay.visible = false
        loadingOverlay.opacity = 0
        loadingOverlay.y = 0
        pendingTargetIndex = -1
        isLoadingSwitching = false
        _waitIndicatorFinished = false
        _targetExpansionFinished = false

        loadingFailed(targetIdx, errorString)
        _trace("helper.loading_failed.done", targetIdx)
    }

    // ==================== Content 内容 ====================
    Connections {
        function onExpandStarted() { helper._beginTargetExpansion() }
        function onCollapseFinished() { helper._completeLoadingCollapse() }
        function onExpandFinished() { helper._completeTargetExpansion() }
        target: helper.pageTransition
    }

    // Public QML loading page matching SplashScreen 公开的 SplashScreen 同款 QML 加载页
    QMLPage {
        id: loadingOverlay

        objectName: "lazyLoadingOverlay"
        width: parent ? parent.width : 0
        height: parent ? parent.height : 0
        text: helper.loadingText
        // Keep the loading surface transparent so the window Mica backdrop remains visible.
        // 保持加载表面透明，让窗口云母背板持续可见。
        backgroundColor: Enums.transparent
        running: visible && opacity > 0
        visible: false
        opacity: 0
        y: 0
        x: 0
        scale: 1
        z: Enums.zIndex.controls

        onFinished: helper._completeWaitIndicatorExit()
    }

    ParallelAnimation {
        id: loadingOverlayEnterAnimation

        NumberAnimation {
            target: loadingOverlay
            property: "x"
            to: 0
            duration: helper.loadingAnimationDuration
            easing.type: Easing.OutCubic
        }
        NumberAnimation {
            target: loadingOverlay
            property: "y"
            to: 0
            duration: helper.loadingAnimationDuration
            easing.type: Easing.OutCubic
        }
        NumberAnimation {
            target: loadingOverlay
            property: "scale"
            to: 1
            duration: helper.loadingAnimationDuration
            easing.type: Easing.OutCubic
        }
        NumberAnimation {
            target: loadingOverlay
            property: "opacity"
            to: 1
            duration: helper.loadingAnimationDuration
            easing.type: Easing.OutCubic
        }
    }
    
    // Sequential stage timer 串行阶段计时器
    Timer {
        id: stageTimer

        property int targetIndex: 0
        property bool _activationPhase: false
        property bool _renderPhase: false

        // The activation budget is measured from collapse start, so subtract the
        // collapse that already elapsed. Read it off the transition in use, not
        // the global token: coverDuration is overridable per site, and reading
        // the token would silently use the wrong number for such a caller.
        // 激活预算从收紧开始计算, 故减去已经花掉的收紧时长。取实际在用过渡上的值
        // 而非全局 token: coverDuration 可单点覆盖, 读 token 会让这类调用方静默
        // 用错数。
        readonly property int _elapsedCollapse:
            helper.pageTransition
            && typeof helper.pageTransition.coverDuration === "number"
                ? helper.pageTransition.coverDuration
                : Enums.lazyLoadingTransitionMetrics.coverDuration

        objectName: "lazyLoaderActivateTimer"
        interval: _activationPhase
                  ? Math.max(
                        Enums.duration.tick,
                        helper.loaderActivationDelay - _elapsedCollapse)
                  : (_renderPhase
                     ? Enums.duration.ultraFast : Enums.duration.tick)
        repeat: !_activationPhase && !_renderPhase
        onTriggered: {
            if (_activationPhase) {
                helper._activateLoaderAndStartPolling(targetIndex)
                return
            }
            if (_renderPhase) {
                helper._completePageRender(targetIndex)
                return
            }
            helper._pollLoader(targetIndex)
        }
    }
}
