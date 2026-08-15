// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import "./_internal"

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
        if (window.visible) {
            animHelper.restoreVisibleState()
        }
    }
    function _startAcceptedClose() {
        _closeInProgress = true
        animHelper.animatedClose()
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
    function prewarmCloseAnimation() { animHelper.prewarmCloseAnimation() }

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
    // Reapply after the native HWND/taskbar button exists so Windows Shell does
    // not keep the generic icon cached from first show. 原生窗口与任务栏按钮
    // 就绪后再次同步，避免 Windows Shell 保留首次显示时的通用图标缓存。
    onNativeHookReady: Qt.callLater(function() {
        window._syncTaskbarIcon("nativeHookReady")
    })
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
            // Hold the first native close request until the dissolve finishes.
            // 首次原生关闭请求先拦住，等渐隐动画完成后再真正销毁窗口。
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
    // 背景: 窗口 opacity 初值为 0(invisible),靠 startShow() 动画拉到 1;
    // 关闭动画 closeAnim 会把 opacity 设回 0。下游"隐藏到托盘"再调裸 show()
    // 恢复时,opacity 仍停在 0 → layered 窗口 alpha=0 完全透明 → 窗口"打开了"
    // 却完全看不见(实测 GetLayeredWindowAttributes alpha=0)。这里在 visible
    // 由 false→true 且 opacity 仍接近 0 时自动补一次 startShow,使所有下游
    // (含直接调 QWindow.show() 的)无需改调用方即可正确恢复显示。
    // 守卫 opacity < 0.5: 避免与正常启动序列(startShow 已在跑)/最大化还原
    //   (opacity 已是 1)重复触发动画。
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
        targetItem: windowFrameLayer.frame
        closeCornerRadius: windowFrameLayer.frame.radius
        onCloseCallback: function() {
            _closeDesktopNotifications()
            var closed = window.close()
            if (closed === false) {
                window._cancelCloseRequest()
            }
        }
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

    Timer {
        id: _resizeHandlesTimer

        interval: Enums.window.resizeHandlesDelayMs
        repeat: false
        onTriggered: {
            _resizeHandlesReady = true
        }
    }

    // QML shadow host. QML 阴影宿主。
    Loader {
        id: shadowHost
        property var hostWindow: window

        anchors.fill: parent
        active: !isMaximized && _useQmlShadow
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
