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
    required property var pageTransition // Shared page-circle transition 共享页面圆形过渡
    
    // ==================== Public Props 公开属性 ====================
    property string loadingText: { Translator._v; return Translator.tr("loading") }
    property int loaderActivationDelay: Enums.duration.none  // Extra delay before Loader activation Loader 激活前额外延迟

    // ==================== Internal Props 内部属性 ====================
    property int pendingTargetIndex: -1
    property bool isLoadingSwitching: false
    property int internalLastIndex: 0
    property int _observedLoaderIndex: -1
    property int _observedLoaderStatus: Loader.Null
    property bool _waitIndicatorFinished: false
    property bool _targetExpansionFinished: false
    
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
            _stopStageTimer()
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

    function _completePageRender(targetIdx) {
        if (targetIdx !== pendingTargetIndex) return

        _trace("helper.page_render.begin", targetIdx)
        var prevIdx = internalLastIndex
        internalLastIndex = targetIdx
        _trace("helper.loading_complete.emit_begin", targetIdx)
        loadingComplete(targetIdx, prevIdx)
        _trace("helper.loading_complete.emit_done", targetIdx)
        var targetLoader = loaders[targetIdx]
        pageTransition.expand(targetLoader)
        _trace("helper.page_render.done", targetIdx)
    }

    function _beginTargetExpansion() {
        if (pendingTargetIndex < 0) return

        _trace("helper.page_expand.begin", pendingTargetIndex)
        if (!loadingOverlay.visible) {
            _waitIndicatorFinished = true
            _finalizeLoadingSwitch()
            return
        }
        loadingOverlay.finish()
    }

    function _completeWaitIndicatorExit() {
        if (pendingTargetIndex < 0) return

        _waitIndicatorFinished = true
        _trace("helper.wait_indicator.finish", pendingTargetIndex)
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

    function _completeLoadingCollapse() {
        var targetIdx = pendingTargetIndex
        if (targetIdx < 0) return

        _trace("helper.page_collapse.finish", targetIdx)
        loadingOverlay.start()
        loadingOverlay.y = 0
        loadingOverlay.opacity = 1
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
        anchors.fill: parent
        text: helper.loadingText
        // Keep the loading surface transparent so the window Mica backdrop remains visible.
        // 保持加载表面透明，让窗口云母背板持续可见。
        backgroundColor: Enums.transparent
        running: visible && opacity > 0
        visible: false
        opacity: 0
        y: 0
        z: Enums.zIndex.controls

        onFinished: helper._completeWaitIndicatorExit()
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
