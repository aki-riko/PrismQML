// NavigationWindowLoading - Python page loading state machine Python 页面加载状态机
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function start(window, index) {
    window._pythonPendingIndex = index
    window._pythonLazyCollapseComplete = false
    window._pythonLoadingFinishRequested = false
    window._pythonRevealScheduled = false
    window._pythonLoading = false
    if (window.stackedWidget && window.stackedWidget._beginPythonLazySwitch) {
        if (window.stackedWidget._beginPythonLazySwitch(index)) return
    }
    window._handlePythonLazyCollapseFinished(index)
}

function finish(window) {
    window._pythonLoadingFinishRequested = true
    // Keep the lightweight host contract synchronous when no stacked
    // widget owns a visual transition. 没有 StackedWidget 管理视觉过渡时，
    // 保留轻量宿主的同步完成语义。
    if (!window.stackedWidget && window._pythonLazyCollapseComplete) {
        window._completePythonLoadingVisual(window._pythonPendingIndex)
        return
    }
    // Match the QML pageSources path once both visual prerequisites already
    // exist: start target expansion in this completion callback instead of
    // forcing one extra loading-ring-only event-loop turn. 页面栈与遮罩均已就绪
    // 时直接在完成回调内启动目标页展开，避免额外强制一轮只显示加载圆环的事件循环。
    if (window._pythonLazyCollapseComplete && window._pythonLoadingOverlay
            && !window._pythonRevealScheduled) {
        resumeLazyReveal(window)
        return
    }
    window._schedulePythonLazyReveal()
}

function handleLazyCollapseFinished(window, index) {
    if (window._pythonPendingIndex >= 0
            && index !== window._pythonPendingIndex) return

    window._pythonLazyCollapseComplete = true
    window._pythonLoading = true
    window._schedulePythonLazyReveal()
}

function handleOverlayReady(window) {
    window._schedulePythonLazyReveal()
}

function scheduleLazyReveal(window) {
    if (!window._pythonLoadingFinishRequested
            || !window._pythonLazyCollapseComplete
            || !window._pythonLoadingOverlay
            || window._pythonRevealScheduled) return

    window._pythonRevealScheduled = true
    Qt.callLater(function() { window._resumePythonLazyReveal() })
}

function resumeLazyReveal(window) {
    window._pythonRevealScheduled = false
    if (!window._pythonLoadingFinishRequested
            || !window._pythonLazyCollapseComplete
            || !window._pythonLoadingOverlay) return

    var index = window._pythonPendingIndex
    if (window.stackedWidget && index >= 0
            && window.stackedWidget._completePythonLazySwitch) {
        if (window.stackedWidget._completePythonLazySwitch(index)) return
    }
    window._completePythonLoadingVisual(index)
}

function completeVisual(window, index) {
    if (window._pythonPendingIndex >= 0
            && index !== window._pythonPendingIndex) return

    window._pythonPendingIndex = -1
    window._pythonLazyCollapseComplete = false
    window._pythonLoadingFinishRequested = false
    window._pythonRevealScheduled = false
    if (window._pythonLoadingOverlay && window._pythonLoadingOverlay.finish) {
        window._pythonLoadingOverlay.finish()
    }
    window._pythonLoading = false
    window.pythonPageReady(index)
}

function beginVisualExit(window, index) {
    if (window._pythonPendingIndex >= 0
            && index !== window._pythonPendingIndex) return
    if (window._pythonLoadingOverlay && window._pythonLoadingOverlay.finish) {
        window._pythonLoadingOverlay.finish()
    }
}

function markPageReady(window, index) {
    if (index < 0) return
    if (window._pythonReadyIndexes.indexOf(index) < 0) {
        var readyIndexes = window._pythonReadyIndexes.slice()
        readyIndexes.push(index)
        window._pythonReadyIndexes = readyIndexes
    }
    if (window.stackedWidget && window.stackedWidget._markPythonPageReady) {
        window.stackedWidget._markPythonPageReady(index)
    }
}

function syncReadyPages(window) {
    if (!window.stackedWidget
            || !window.stackedWidget._markPythonPageReady) return
    for (var index = 0; index < window._pythonReadyIndexes.length; index++) {
        window.stackedWidget._markPythonPageReady(
            window._pythonReadyIndexes[index]
        )
    }
}
