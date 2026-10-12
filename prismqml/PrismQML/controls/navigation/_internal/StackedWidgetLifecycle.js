// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// StackedWidgetLifecycle - Synchronous host signal handling 堆叠页面同步宿主信号处理

function onCompleted(host) {
    if (host.dynamicStack && host._dynamicDepth < 0) host._dynamicDepth = host.count
    host._indexClampReady = true
    host._clampPageIndexes()
    host.profileTime("Component.onCompleted count=" + host.count +
                     ", lazyLoading=" + host.lazyLoading +
                     ", sourceMode=" + host._useSourceMode)
    host._preloadLazyHelperWhenReady("completed")
    if (host.lazyLoading && host._useSourceMode && !host._isPageLoaded(host._displayIndex)) {
        host._pendingLazySwitchIndex = host._displayIndex
    }
}

function onCountChanged(host) {
    if (host._indexClampReady) host._clampPageIndexes()
}

function onLazyLoadingChanged(host, eagerHelper) {
    if (host.lazyLoading) {
        eagerHelper.cancel()
        host._preloadLazyHelperWhenReady("lazyLoadingChanged")
    } else {
        eagerHelper.start()
    }
}

function onPageLoaded(host, eagerHelper, index) {
    if (index === host._displayIndex && host._pendingLazySwitchIndex === index) {
        host._pendingLazySwitchIndex = -1
    }
    if (index === host._displayIndex) {
        host._preloadLazyHelperWhenReady("pageLoaded index=" + index)
    }
    if (!host.lazyLoading && index === eagerHelper.requestedIndex &&
            index !== host._displayIndex && index === host.currentIndex) {
        eagerHelper.requestedIndex = -1
        host.previousIndex = host._displayIndex
        host._doAnimation(host._displayIndex, index)
        host._displayIndex = index
    }
}

function onCurrentIndexChanged(host, lazyLoader, eagerHelper) {
    host._traceLazyStage("stacked.current_index_changed", host.currentIndex)
    host.profileTime("currentIndex changed to " + host.currentIndex)
    if (host.currentIndex === host._displayIndex) {
        host._cancelPendingLazySwitch("returned-to-visible")
        return
    }
    if (host.currentIndex < 0 || host.currentIndex >= host.count) return

    var helper = lazyLoader.item
    if (helper && helper.pendingTargetIndex >= 0
            && helper.pendingTargetIndex !== host.currentIndex) {
        host._cancelPendingLazySwitch("retargeted")
    }

    if (host._pythonLazyTransitionTargetIndex >= 0 &&
            host._pythonLazyTransitionTargetIndex !== host.currentIndex) {
        host._cancelPythonLazySwitch(
            host._pythonLazyTransitionTargetIndex, host.currentIndex)
        return
    }

    if (host.lazyLoading && !host._isPageLoaded(host.currentIndex)) {
        if (!host._pythonPageMode) {
            host._showLazyLoadingAndSwitch(host.currentIndex)
        }
    } else if (!host.lazyLoading && host._useSourceMode
            && !host._isPageLoaded(host.currentIndex)) {
        eagerHelper.request(host.currentIndex)
    } else {
        // Loaded pages always use the configured StackedWidget transition.
        // 已加载页面始终使用 StackedWidget 配置的常规切页动画。
        host.previousIndex = host._displayIndex
        host._doAnimation(host._displayIndex, host.currentIndex)
        host._displayIndex = host.currentIndex
    }
}
