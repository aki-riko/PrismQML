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
