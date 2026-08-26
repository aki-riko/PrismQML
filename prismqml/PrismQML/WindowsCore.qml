// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import "./_internal"
import "./controls/navigation"

// WindowsCore - Base class for all Window 所有 Window 的基类
// Pure QML: rounded corners + shadow + titlebar + resize 纯QML实现
// Supports top/left title bar layout 支持顶部/左侧标题栏布局
Window {
    id: window

    // ==================== Public Props 公开属性 ====================
    default property alias content: windowFrameLayer.contentData
    property alias leftPanelContent: windowFrameLayer.leftPanelData
    property bool startupProfilingVerbose: false
    readonly property color accentColor: Enums.accentColor
    property bool closeRequestAccepted: true
    property int titleBarPosition: Enums.windowType.title_bar_top
    // Left panel width for the left layout. 左侧布局的面板宽度。
    property int leftPanelWidth: Enums.window.navPanelMinWidth
    property string windowIcon: ""
    // Skip the color overlay for multicolor icons. 彩色图标跳过颜色覆盖。
    property bool windowIconColored: false
    property int titleBarHeight: Enums.window.titleBarHeight
    property int captionButtonHeight: Enums.window.captionButtonHeight
    readonly property int captionButtonWidth: Enums.window.captionButtonWidth
    property int titleBarLeftMargin: Enums.window.titleBarLeftMargin
    property string windowTitle: ""
    property int windowRadius: Enums.surfaceRadius(Enums.radius.large)
    property int shadowSize: Enums.window.qmlShadowSize
    property color windowColor: Enums.backgroundColor
    property int shadowMode: Enums.windowShadow.mode_auto
    property int closeAnimationType: Enums.animation.lazy_circle
    property Component closeAnimation: null

    // ==================== Internal Props 内部属性 ====================
    readonly property real _appStartTime: Date.now()
    property real _lastStartupProfileTime: _appStartTime
    property real _lastStartupDetailTime: _appStartTime
    readonly property bool _startupProfilingVerboseActive:
        startupProfilingVerbose ||
        (typeof PrismQmlStartupProfileVerbose !== "undefined" && PrismQmlStartupProfileVerbose)
    readonly property alias _showAnimationStarted: nativeWindowStartup.showAnimationStarted
    readonly property alias _showAnimationStartCount: nativeWindowStartup.showAnimationStartCount
    readonly property alias _startupPresentationReady:
        nativeWindowStartup.startupPresentationReady
    property alias _animScale: animHelper.animScale
    property alias _animOpacity: animHelper.animOpacity
    property bool _closeInProgress: false
    property bool _closeCompletionPending: false
    property bool _closeSourceWasVisible: true
    property bool _titleChromeReady: true
    property bool _resizeHandlesReady: false
    property bool _dwmInitializationDone: false
    readonly property bool _platformSupportsNative: ShadowManager ? ShadowManager.useNative : false
    readonly property bool _useNativeShadow: {
        if (Enums.isVintageTicket) return false
        if (shadowMode === Enums.windowShadow.mode_none) return false
        if (shadowMode === Enums.windowShadow.mode_native) return true
        if (shadowMode === Enums.windowShadow.mode_qml) return false
        return _platformSupportsNative
    }
    readonly property bool _useQmlShadow: {
        if (Enums.isVintageTicket) return false
        if (shadowMode === Enums.windowShadow.mode_none) return false
        if (shadowMode === Enums.windowShadow.mode_native) return false
        if (shadowMode === Enums.windowShadow.mode_qml) return true
        return !_platformSupportsNative
    }

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isLeftLayout: titleBarPosition === Enums.windowType.title_bar_left
    readonly property bool isMaximized: window.visibility === Window.Maximized
    readonly property int margin: isMaximized ? 0 : (_useNativeShadow ? 0 : (_useQmlShadow ? shadowSize : 0))

    // ==================== Signals 信号 ====================
    // Fired after DWM-touching init done (shadow + native hook attached) 通知子类: DWM 相关初始化完成
    // 子类可挂这个信号设置 Mica 等会被 SWP_FRAMECHANGED 重置的 DWM 属性
    signal nativeHookReady()
    // Fired synchronously after a close request is accepted, before HWND teardown.
    // 关闭请求确认后、HWND 销毁前同步触发。
    signal nativeCloseAccepted()
    // Fired before a user/system close request is accepted. Handlers may set
    // closeRequestAccepted to false to keep the window alive.
    signal closeRequested()

    // ==================== Internal Methods 内部方法 ====================
    function logTime(msg) { console.log("[" + Math.round(Date.now() - _appStartTime) + "ms]", msg) }
    function profileTime(msg) {
        if (!_startupProfilingVerboseActive) return
        var now = Date.now()
        console.debug("[启动剖析] WindowsCore " + msg + ": +" +
                    Math.round(now - _lastStartupProfileTime) + "ms / total " +
                    Math.round(now - _appStartTime) + "ms")
        _lastStartupProfileTime = now
    }
    function profileDetail(msg) {
        if (!_startupProfilingVerboseActive) return
        var now = Date.now()
        console.debug("[启动剖析] WindowsCore DETAIL " + msg + ": +" +
                    Math.round(now - _lastStartupDetailTime) + "ms / total " +
                    Math.round(now - _appStartTime) + "ms")
        _lastStartupDetailTime = now
    }
    function profileDetailState(msg) {
        if (!_startupProfilingVerboseActive) return
        profileDetail(msg + " visible=" + visible +
                      " size=" + Math.round(width) + "x" + Math.round(height) +
                      " shadowMode=" + shadowMode +
                      " native=" + _useNativeShadow +
                      " qmlShadow=" + _useQmlShadow +
                      " leftLayout=" + _isLeftLayout)
    }
    function _cancelCloseRequest() {
        _closeInProgress = false
        _closeCompletionPending = false
        closeFrameWaiter.cancel()
        closeTransition.stop()
        // A cancelled close must put the native shadow back, or the window
        // stays on screen without it. 取消关闭必须把原生阴影装回去, 否则窗口留在
        // 屏上却没了阴影。
        _setNativeShadowForClose(true)
        windowFrameLayer.visible = _closeSourceWasVisible
        if (window.visible) {
            animHelper.restoreVisibleState()
        }
    }
    function _startAcceptedClose() {
        _closeInProgress = true
        _closeSourceWasVisible = windowFrameLayer.visible
        // The native shadow is a DWM non-client rendering policy on the hwnd,
        // so no QML layer mask can clip it. Left on, DWM keeps painting a
        // rectangular shadow around the full window bounds while the circle
        // collapses, leaving the periphery visibly unclipped. Drop it for the
        // duration of the close only; _cancelCloseRequest restores it.
        // 原生阴影是 hwnd 上的 DWM 非客户区渲染策略, QML 的 layer 遮罩裁不到它。
        // 不关掉的话, 圆环收紧期间 DWM 仍按整窗矩形画阴影, 外围就明显没被裁掉。
        // 仅在关闭期间撤掉; _cancelCloseRequest 会恢复。
        _setNativeShadowForClose(false)
        closeTransition.collapse(windowFrameLayer)
    }
    function _setNativeShadowForClose(enabled) {
        if (!ShadowManager || !_useNativeShadow) return
        if (enabled) {
            ShadowManager.enableShadowForWindow(window)
        } else {
            ShadowManager.disableShadowForWindow(window)
        }
    }
    function _completeAcceptedClose() {
        if (!_closeInProgress) return
        _closeDesktopNotifications()
        var closed = window.close()
        if (closed === false) _cancelCloseRequest()
    }
    function _armAcceptedClose() {
        if (!_closeInProgress) return
        _closeCompletionPending = true
        closeFrameWaiter.arm()
    }
    function _handleCloseFrameEnd() {
        if (!_closeCompletionPending) return
        _closeCompletionPending = false
        Qt.callLater(window._completeAcceptedClose)
    }
    function _closeDesktopNotifications() {
        var component = Qt.createComponent(Qt.resolvedUrl("_internal/DesktopNotificationCloser.qml"))
        if (component.status !== Component.Ready) {
            console.warn("DesktopNotificationCloser not ready:", component.errorString())
            return
        }
        var closer = component.createObject(window)
        if (!closer) return
        closer.closeAll()
        closer.destroy()
    }
    function _syncTaskbarIcon(reason) {
        if (!windowIcon || typeof WindowHelper === "undefined" || !WindowHelper) return
        profileTime("WindowHelper.setAppIcon " + reason + " start")
        WindowHelper.setAppIcon(windowIcon)
        profileTime("WindowHelper.setAppIcon " + reason + " done")
    }
    function _syncNativeCorner(reason) {
        if (!_dwmInitializationDone ||
                typeof MicaManager === "undefined" || !MicaManager ||
                typeof MicaManager.setWindowCorner !== "function") return false
        profileTime("WindowsCore sync native corner " + reason + " start")
        var success = MicaManager.setWindowCorner(window, windowRadius > 0)
        profileTime("WindowsCore sync native corner " + reason +
                    " done success=" + success)
        return success
    }

    // ==================== Public Methods 公开方法 ====================
    function prepareBeforeShow() { nativeWindowStartup.prepareBeforeShow() }
    function requestClose() {
        if (_closeInProgress) return
        closeRequestAccepted = true
        closeRequested()
        if (closeRequestAccepted) {
            _startAcceptedClose()
        } else {
            _cancelCloseRequest()
        }
    }
    function animatedClose() {
        requestClose()
    }
    function restoreVisibleState() { animHelper.restoreVisibleState() }
    function ensureVisiblePaintState(reason) {
        if (_closeInProgress || !window.visible) return
        // Initial exposure stays transparent until Splash reaches frameSwapped.
        // Splash 首帧提交前保持透明，避免原生空白表面提前曝光。
        if (!nativeWindowStartup.showAnimationStarted) return
        if (window.opacity >= 0.99 && _animOpacity >= 0.99 && _animScale >= 0.99) return
        profileTime("ensureVisiblePaintState " + reason)
        animHelper.restoreVisibleState()
    }
    function animatedMinimize() { animHelper.animatedMinimize() }
    function animatedMaximize() { animHelper.animatedMaximize() }
    function animatedRestore() { animHelper.animatedRestore() }

    // ==================== Size 尺寸 ====================
    width: Enums.window.defaultWidth
    height: Enums.window.defaultHeight
    minimumWidth: Enums.window.minimumWidth
    minimumHeight: Enums.window.minimumHeight
    // QML-created windows should show by default. Python WindowCore injects
    // visible: false into its generated root QML before calling Window.show().
    visible: true
    opacity: Enums.opacityLevel.invisible
    color: Enums.transparent
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint
    title: windowTitle  // Sync to native Window.title for taskbar 同步到原生标题用于任务栏显示

    onWindowIconChanged: _syncTaskbarIcon("windowIconChanged")
    onWindowRadiusChanged: _syncNativeCorner("windowRadiusChanged")
    // Reapply after the native HWND/taskbar button exists so Windows Shell does
    // not keep the generic icon cached from first show. 原生窗口与任务栏按钮
    // 就绪后再次同步，避免 Windows Shell 保留首次显示时的通用图标缓存。
    onNativeHookReady: {
        _syncNativeCorner("nativeHookReady")
        Qt.callLater(function() {
            window._syncTaskbarIcon("nativeHookReady")
        })
    }
    Component.onCompleted: {
        profileTime("Component.onCompleted start; NativeWindow defined=" +
                    (typeof NativeWindow !== "undefined"))
        animHelper.animScale = 0.95
        animHelper.animOpacity = 0
        profileTime("初始化动画状态")
        // 延后 native hook: winId()/style 写入在冷启动可达 90ms+,不要阻塞 loadData。
        // Native startup helper finalizes attach after winId becomes available.
        // 原生启动助手会在 winId 可用后完成 attach。
        nativeWindowStartup.start()
        profileTime("nativeWindowStartup.start")
        _resizeHandlesTimer.start()
        profileTime("_resizeHandlesTimer.start")
    }
    onClosing: (close) => {
        if (!_closeInProgress) {
            closeRequestAccepted = true
            closeRequested()
            if (!closeRequestAccepted) {
                close.accepted = false
                _cancelCloseRequest()
                return
            }
            // Leave the first native close delivery before issuing the accepted close.
            // 首次原生关闭请求先退出当前分发, 再发起已接受的真实关闭。
            close.accepted = false
            _startAcceptedClose()
            return
        }
        nativeCloseAccepted()
        // 注意: onClosing 在窗口收到「任何」关闭请求时都会触发,包括上层
        // event.ignore() 拦截后「隐藏到托盘」的场景 —— 此时窗口并未销毁,
        // 仍要继续使用。这里绝不能 detach NativeWindowHook,否则 hwnd 的
        // WS_CAPTION/THICKFRAME style 被还原 + 移出 NCCALCSIZE 过滤集合,
        // 之后再 show() 无法点亮 WS_VISIBLE,主窗口永久无法恢复显示。
        // detach 的正确时机是窗口「真正销毁」时,见下方 Component.onDestruction。
    }
    // 窗口真正销毁时才解除 native hook (而非每次 closing)。
    // QML 对象 destroy() / 引擎析构会触发此处;detach 内部对未 attach 的
    // hwnd 有保护,重复或无效调用安全。
    // 守卫必须同时挡 undefined 和 null: 析构期 context property NativeWindow
    // 可能已被置 null (typeof null === "object" 不等于 "undefined",单用
    // typeof 守卫会漏过 null 导致 "Cannot call method 'detach' of null")。
    Component.onDestruction: {
        if (typeof NativeWindow !== "undefined" && NativeWindow) {
            try {
                if (typeof NativeWindow.detach !== "function" ||
                        NativeWindow.detach(window) !== true) {
                    console.warn("NativeWindow.detach failed during window destruction")
                }
            } catch (error) {
                console.warn("NativeWindow.detach raised during window destruction:", error)
            }
        }
    }
    on_UseNativeShadowChanged: {
        profileTime("_useNativeShadow changed: " + _useNativeShadow)
        if (!_dwmInitializationDone) {
            profileTime("_useNativeShadow change skipped before DWM initialization")
            return
        }
        if (!ShadowManager) return
        if (_useNativeShadow) {
            profileTime("ShadowManager.enableShadowForWindow runtime start")
            ShadowManager.enableShadowForWindow(window)
            profileTime("ShadowManager.enableShadowForWindow runtime done")
        } else {
            profileTime("ShadowManager.disableShadowForWindow runtime start")
            ShadowManager.disableShadowForWindow(window)
            profileTime("ShadowManager.disableShadowForWindow runtime done")
        }
    }
    onVisibilityChanged: {
        if (window.visibility !== Window.Hidden && window.visibility !== Window.Minimized) {
            ensureVisiblePaintState("visibilityChanged")
        }
    }

    // 从隐藏恢复显示时重新播放显示动画,把 opacity 拉回 1。
    // 背景: 窗口 opacity 初值为 0(invisible),首个完整帧后由 startShow()
    // 直接设为 1。若下游在首帧门槛期间隐藏后再调用裸 show(), layered 窗口
    // 可能仍保持 alpha=0。这里在 visible 由 false→true 时恢复完整绘制状态,
    // 使直接调用 QWindow.show() 的下游也能正确恢复显示。
    onVisibleChanged: ensureVisiblePaintState("visibleChanged")

    // ==================== Content 内容 ====================
    NativeWindowStartupHelper {
        id: nativeWindowStartup
        targetWindow: window
        animationHelper: animHelper
        useNativeShadow: window._useNativeShadow
    }

    WindowAnimationHelper {
        id: animHelper
        targetWindow: window
    }

    PageTransition {
        id: closeTransition

        objectName: "windowClosePageTransition"
        anchors.fill: parent
        animationType: window.closeAnimationType
        customAnimation: window.closeAnimation
        collapseToCenter: true
        onCollapseFinished: Qt.callLater(window._armAcceptedClose)
    }

    WindowCloseFrameWaiter {
        id: closeFrameWaiter

        targetWindow: window
        onCompleted: window._handleCloseFrameEnd()
    }

    // Listen to ConfigManager directly. 直接监听 ConfigManager 信号。
    Connections {
        function onDwmShadowChanged() {
            if (!ShadowManager) return
            var enabled = ConfigManager.dwmShadow
            logTime("ConfigManager.dwmShadow changed: " + enabled)
            if (enabled && window._useNativeShadow) {
                ShadowManager.enableShadowForWindow(window)
            } else {
                ShadowManager.disableShadowForWindow(window)
            }
        }

        target: typeof ConfigManager !== "undefined" ? ConfigManager : null
    }

    WindowsResizeHandlesTimer {
        id: _resizeHandlesTimer
        host: window
    }

    // QML shadow host. QML 阴影宿主。
    Loader {
        id: shadowHost

        property var hostWindow: window

        objectName: "windowQmlShadowHost"

        anchors.fill: parent
        // This host is a sibling of windowFrameLayer, so the close circle's
        // layer mask never reaches it. It draws an opaque windowColor rect at
        // full window size, which stayed visible under the shrinking circle as
        // a rectangular blank. Drop it for the close collapse only: the shadow
        // belongs to the periphery being clipped away. Gated on
        // _closeInProgress, which only the window close path sets, so lazy page
        // transitions are unaffected.
        // 本宿主是 windowFrameLayer 的兄弟节点, 关闭圆环的 layer 遮罩到不了它。它
        // 以整窗尺寸画一个不透明的 windowColor 矩形, 于是在收紧的圆下面残留成一块
        // 矩形留白。仅在关闭收紧时去掉它: 阴影本就属于要被裁掉的外围。以
        // _closeInProgress 作门, 该标志只由窗口关闭路径设置, 故不影响懒加载页面过渡。
        active: !isMaximized && _useQmlShadow && !_closeInProgress
        visible: active
        opacity: _animOpacity
        scale: _animScale
        asynchronous: true
        source: active ? Qt.resolvedUrl("_internal/QmlShadowHost.qml") : ""
    }

    WindowsCoreFrame {
        id: windowFrameLayer

        anchors.fill: parent
        targetWindow: window
    }
}
