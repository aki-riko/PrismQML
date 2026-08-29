// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// StackedLazyController - Lazy page switching orchestration
// StackedLazyController - 懒加载页面切换编排
Item {
    id: controller

    // ==================== Required Props 必需属性 ====================
    required property Item host
    required property Loader lazyHelperLoader
    required property Item pageTransition
    required property Item animations

    // ==================== Public Methods 公开方法 ====================
    function preloadLazyHelperWhenReady(reason) {
        if (!host.lazyLoading || !host._isPageLoaded(host._displayIndex)) return
        host._ensureLazyHelperLoaded(reason)
    }

    function cancelPendingLazySwitch(reason) {
        var pendingIndex = host._pendingLazySwitchIndex
        var helper = lazyHelperLoader.item
        var helperPendingIndex = helper && helper.pendingTargetIndex !== undefined
                ? helper.pendingTargetIndex : -1
        if (pendingIndex < 0 && helperPendingIndex < 0) return false

        host._pendingLazySwitchIndex = -1
        if (helper && helper.cancelPendingLoad) helper.cancelPendingLoad()
        host._updateVisibility(host._displayIndex)
        host._traceLazyStage(
            "stacked.lazy_switch.cancel", host.currentIndex,
            "reason=" + reason + " pending=" + pendingIndex +
            " helperPending=" + helperPendingIndex)
        return true
    }

    function showLazyLoadingAndSwitch(index) {
        host._traceLazyStage("stacked.switch_request", index)
        host._pendingLazySwitchIndex = index
        host._ensureLazyHelperLoaded("switch target=" + index)
        if (!lazyHelperLoader.item) return
        if (!lazyHelperLoader.active) {
            lazyHelperLoader.active = true
            host.profileTime("lazyHelper deferred load reactivated target=" + index)
            return
        }
        flushPendingLazySwitch()
    }

    function flushPendingLazySwitch() {
        if (host._pendingLazySwitchIndex < 0) return
        if (!lazyHelperLoader.item) return

        var target = host._pendingLazySwitchIndex
        host._pendingLazySwitchIndex = -1
        host._traceLazyStage("stacked.helper_dispatch.begin", target)
        lazyHelperLoader.item.showLoadingAndSwitch(target)
        host._traceLazyStage("stacked.helper_dispatch.done", target)
    }

    function configureLazyHelper(item) {
        if (!item) return

        item.width = Qt.binding(function() { return lazyHelperLoader.width })
        item.height = Qt.binding(function() { return lazyHelperLoader.height })
        item.loaders = Qt.binding(function() { return host._loaders })
        item.targetIndex = Qt.binding(function() { return host.currentIndex })
        item.currentVisibleIndex = Qt.binding(function() { return host._displayIndex })
        item.loadingText = Qt.binding(function() { return host.loadingText })
        item.loaderActivationDelay = Qt.binding(
            function() { return host.lazyActivationDelay })
        item.isPageLoadedFunc = host._isPageLoaded
        item.isPageLoadFailedFunc = host._isPageLoadFailedFunc
        item.pageLoadErrorFunc = host._pageLoadErrorFunc
        item.activateLoaderFunc = host._activateLoader
        item.diagnosticFunc = host._traceLazyStage
        item.pageTransition = pageTransition
        item.loadingComplete.connect(host._handleLazyLoadingComplete)
        item.loadingFailed.connect(function(targetIdx, errorString) {
            host._traceLazyStage("stacked.loading_failed", targetIdx)
            host.profileTime(
                "lazyHelper loadingFailed target=" + targetIdx +
                ", error=" + errorString)
            host.pageLoadFailed(targetIdx, errorString)
        })
    }

    function beginPythonLazySwitch(targetIndex) {
        host._pythonLazyTransitionTargetIndex = targetIndex
        host._pythonLazyRevealRequested = false
        return pageTransition.collapse(host.widget(host._displayIndex))
    }

    function startPythonLazyExpansion(targetIndex) {
        var targetWidget = host.widget(targetIndex)
        if (!targetWidget) {
            cancelPythonLazySwitch(targetIndex)
            return
        }

        host.previousIndex = host._displayIndex
        host._displayIndex = targetIndex
        // Match the pageSources path exactly: the regular enter animation keeps
        // the minimum-radius reveal frame transparent, so the target appears as
        // a direct expansion instead of a standalone center circle.
        // 与 pageSources 路径完全一致：常规入场动画会让最小半径揭幕帧保持透明，
        // 目标页因此表现为直接展开，而不是先单独显示中心圆圈。
        if (animations.prepareEnter(targetIndex)) {
            host._doEnterAnimation(targetIndex)
        }
        pageTransition.expand(targetWidget)
    }

    function cancelPythonLazySwitch(targetIndex) {
        pageTransition.stop()
        host._updateVisibility(host._displayIndex)
        host._pythonLazyTransitionTargetIndex = -1
        host._pythonLazyRevealRequested = false
        host.pythonLazyTransitionFinished(targetIndex)
    }

    function completePythonLazySwitch(targetIndex) {
        if (targetIndex < 0 || targetIndex >= host.count
                || targetIndex !== host.currentIndex) return false

        if (host._pythonPageMode && !host._isPageLoaded(targetIndex)) {
            cancelPythonLazySwitch(targetIndex)
            return true
        }

        host._pythonLazyTransitionTargetIndex = targetIndex
        host._pythonLazyRevealRequested = true
        if (pageTransition.collapsed || !pageTransition.active) {
            startPythonLazyExpansion(targetIndex)
        }
        return true
    }

    function handlePythonLazyCollapseFinished() {
        var targetIndex = host._pythonLazyTransitionTargetIndex
        if (targetIndex < 0) return
        host.pythonLazyCollapseFinished(targetIndex)
    }

    function handlePythonLazyExpandStarted() {
        var targetIndex = host._pythonLazyTransitionTargetIndex
        if (targetIndex < 0) return
        host.pythonLazyExpansionStarted(targetIndex)
    }

    function handlePythonLazyExpandFinished() {
        var targetIndex = host._pythonLazyTransitionTargetIndex
        if (targetIndex < 0) return
        host._pythonLazyTransitionTargetIndex = -1
        host._pythonLazyRevealRequested = false
        host.pythonLazyTransitionFinished(targetIndex)
    }

    function handleLazyLoadingComplete(targetIdx, prevIdx) {
        host._traceLazyStage("stacked.loading_complete.begin", targetIdx,
                             "previous=" + prevIdx)
        host.profileTime(
            "lazyHelper loadingComplete start target=" + targetIdx +
            ", prev=" + prevIdx)
        // Keep currentIndex declarative; _displayIndex tracks the rendered page.
        // 保持 currentIndex 声明式绑定，由 _displayIndex 跟踪实际显示页面。
        host.previousIndex = host._displayIndex
        host._displayIndex = targetIdx
        if (animations.prepareEnter(targetIdx)) {
            host._doEnterAnimation(targetIdx)
        }
        host.profileTime("lazyHelper loadingComplete done")
        host._traceLazyStage("stacked.loading_complete.done", targetIdx,
                             "previous=" + prevIdx)
    }
}
