.pragma library

function activate(host) {
    if (!host._deferredSplashPending || !host._splashInstance)
        return
    host._deferredSplashPending = false
    host._markSplashVisible()
    if (host.stackedWidget)
        host._dismissSplashWhenReady(host.stackedWidget)
}

function enable(host) {
    host._splashDismissed = false
    host._splashDismissRequested = false
    host._splashDismissSchedulePending = false
    host._splashTimerObject.stop()
    host._deferredSplashPending = true
    host.splashEnabled = true
    activate(host)
}

function dismissWhenReady(host, stack) {
    host.profileTime("NavigationWindowCore _dismissSplashWhenReady start")
    if (host._splashDismissed) {
        host.profileTime("NavigationWindowCore splash already dismissed")
        return
    }
    if (!host._splashInstance) {
        host._splashDismissed = true
        host.profileTime("NavigationWindowCore no splash instance")
        return
    }

    if (!stack || stack._isPageLoaded(stack.currentIndex)) {
        host.profileTime("NavigationWindowCore splash ready immediate")
        host._requestSplashDismiss()
        return
    }

    var target = stack.currentIndex
    function onPageLoaded(index) {
        if (index !== target) return
        stack.pageLoaded.disconnect(onPageLoaded)
        host._splashTimerObject.stop()
        host.profileTime("NavigationWindowCore splash pageLoaded target=" + index)
        host._requestSplashDismiss()
    }
    stack.pageLoaded.connect(onPageLoaded)
    host._splashTimerObject._minimumVisiblePhase = false
    host._splashTimerObject._onTimeout = function() {
        stack.pageLoaded.disconnect(onPageLoaded)
        host.profileTime("NavigationWindowCore splash timeout")
        host._requestSplashDismiss()
    }
    host._splashTimerObject.restart()
    host.profileTime("NavigationWindowCore splash wait pageLoaded target=" + target)
}
