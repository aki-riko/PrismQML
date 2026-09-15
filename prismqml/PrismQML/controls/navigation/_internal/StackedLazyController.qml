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

    // ==================== Internal Props 内部属性 ====================
    // Target waiting for the QML lazy circle to finish. 等待 QML 懒加载圆圈完成的目标。
    property int _qmlLazyTransitionTargetIndex: -1

    // ==================== Public Methods 公开方法 ====================
    function preloadLazyHelperWhenReady(reason) {
        if (!host.lazyLoading || !host._useSourceMode) return
        host._ensureLazyHelperLoaded(reason)
    }

    function cancelPendingLazySwitch(reason) {
        var pendingIndex = host._pendingLazySwitchIndex
        var helper = lazyHelperLoader.item
        var helperPendingIndex = helper && helper.pendingTargetIndex !== undefined
                ? helper.pendingTargetIndex : -1
        var pythonTargetIndex = host._pythonLazyTransitionTargetIndex
        if (pendingIndex < 0 && helperPendingIndex < 0 &&
                pythonTargetIndex < 0) return false

        host._pendingLazySwitchIndex = -1
        _qmlLazyTransitionTargetIndex = -1
        if (helper && helper.cancelPendingLoad) helper.cancelPendingLoad()
        if (pythonTargetIndex >= 0) {
            cancelPythonLazySwitch(pythonTargetIndex)
        }
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

    function showInitialLoading(index) {
        if (!lazyHelperLoader.item || host._isPageLoaded(index)) return
        var helper = lazyHelperLoader.item
        helper.showInitialLoading(index)
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
        // The loading overlay is part of the lazy transition, not the regular
        // page switch. Keep it stationary so slide/fade cannot run alongside
        // the circle collapse/reveal.
        // 加载覆盖层属于懒加载过渡，不属于普通切页；固定为无位移入场，
        // 避免 slide/fade 与圆圈收紧/揭幕同时运行。
        item.loadingAnimationType = Enums.animation.none
        item.loadingAnimationDuration = Qt.binding(
            function() { return host.animationDuration })
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
        // Lazy navigation has one visual owner: the circle transition. Make the
        // target visible before expand() captures it; a second StackedWidget
        // animation would otherwise run on top of the circle.
        // 懒加载导航只允许一个视觉所有者：圆圈过渡。展开前先显示目标页供
        // expand() 抓取，否则第二套 StackedWidget 动画会与圆圈叠加。
        host._updateVisibility(targetIndex)
        pageTransition.expand(targetWidget)
    }

    function cancelPythonLazySwitch(targetIndex, restoreIndex) {
        pageTransition.stop()
        if (restoreIndex !== undefined && restoreIndex >= 0) {
            host._displayIndex = restoreIndex
        }
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
        if (targetIndex >= 0) {
            host._pythonLazyTransitionTargetIndex = -1
            host._pythonLazyRevealRequested = false
            // The expansion restores its own source page on finish. When navigation
            // already moved on, that page is no longer the displayed one, so reassert
            // the displayed page instead of leaving both visible.
            // 揭幕结束时会自行恢复其源页可见性。若导航期间已切走，该页不再是当前显示页，
            // 因此重新校正显示页，避免两页同时可见。
            if (targetIndex !== host._displayIndex) {
                host._updateVisibility(host._displayIndex)
            }
            host.currentChanged(targetIndex)
            host.pythonLazyTransitionFinished(targetIndex)
            return
        }
        if (_qmlLazyTransitionTargetIndex >= 0) {
            var qmlTargetIndex = _qmlLazyTransitionTargetIndex
            _qmlLazyTransitionTargetIndex = -1
            host.currentChanged(qmlTargetIndex)
        }
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
        // Lazy navigation has one visual owner: PageTransition. The target is
        // made visible here and is then revealed by the circle transition.
        // 懒加载导航只允许 PageTransition 负责视觉过渡；此处显示目标页，
        // 随后统一交给圆圈过渡揭幕，禁止叠加 StackedWidget 动画。
        host._updateVisibility(targetIdx)
        _qmlLazyTransitionTargetIndex = targetIdx
        host.profileTime("lazyHelper loadingComplete done")
        host._traceLazyStage("stacked.loading_complete.done", targetIdx,
                             "previous=" + prevIdx)
    }
}
