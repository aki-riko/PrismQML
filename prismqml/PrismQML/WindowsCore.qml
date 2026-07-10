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
    
    // ==================== Startup Timing 启动计时 ====================
    readonly property real _appStartTime: Date.now()
    property real _lastStartupProfileTime: _appStartTime
    property real _lastStartupDetailTime: _appStartTime
    property bool startupProfilingVerbose: false
    readonly property bool _startupProfilingVerboseActive:
        startupProfilingVerbose ||
        (typeof PrismQmlStartupProfileVerbose !== "undefined" && PrismQmlStartupProfileVerbose)

    // ==================== Theme 主题 ====================
    readonly property color accentColor: Enums.accentColor

    function logTime(msg) { console.log("[" + Math.round(Date.now() - _appStartTime) + "ms]", msg) }
    function profileTime(msg) {
        var now = Date.now()
        console.info("[启动剖析] WindowsCore " + msg + ": +" +
                    Math.round(now - _lastStartupProfileTime) + "ms / total " +
                    Math.round(now - _appStartTime) + "ms")
        _lastStartupProfileTime = now
    }
    function profileDetail(msg) {
        if (!_startupProfilingVerboseActive) return
        var now = Date.now()
        console.info("[启动剖析] WindowsCore DETAIL " + msg + ": +" +
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

    // ==================== Signals 信号 ====================
    // Fired after DWM-touching init done (shadow + native hook attached) 通知子类: DWM 相关初始化完成
    // 子类可挂这个信号设置 Mica 等会被 SWP_FRAMECHANGED 重置的 DWM 属性
    signal nativeHookReady()
    // Fired before a user/system close request is accepted. Handlers may set
    // closeRequestAccepted to false to keep the window alive.
    signal closeRequested()
    
    // ==================== Window Props 窗口属性 ====================
    width: Enums.window.defaultWidth
    height: Enums.window.defaultHeight
    minimumWidth: Enums.window.minimumWidth
    minimumHeight: Enums.window.minimumHeight
    // QML-created windows should show by default. Python WindowCore injects
    // visible: false into its generated root QML before calling Window.show().
    visible: true
    opacity: Enums.opacityLevel.invisible
    color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint
    property bool closeRequestAccepted: true
    property bool _closeInProgress: false
    property bool _titleChromeReady: true
    property bool _resizeHandlesReady: false
    
    // ==================== Layout Mode 布局模式 ====================
    property int titleBarPosition: Enums.windowType.title_bar_top
    readonly property bool _isLeftLayout: titleBarPosition === Enums.windowType.title_bar_left
    
    // Left panel width (for left layout) 左侧面板宽度
    property int leftPanelWidth: Enums.window.navPanelMinWidth
    
    // ==================== Appearance 外观 ====================
    property string windowIcon: ""
    property bool windowIconColored: false  // Whether icon is colored (skip color overlay) 图标是否为彩色（跳过颜色覆盖）
    onWindowIconChanged: {
        // Sync window icon to taskbar 同步窗口图标到任务栏
        if (windowIcon && typeof WindowHelper !== "undefined") {
            profileTime("WindowHelper.setAppIcon start")
            WindowHelper.setAppIcon(windowIcon)
            profileTime("WindowHelper.setAppIcon done")
        }
    }
    property int titleBarHeight: Enums.window.titleBarHeight
    property int captionButtonHeight: Enums.window.captionButtonHeight
    readonly property int captionButtonWidth: Enums.window.captionButtonWidth
    property int titleBarLeftMargin: Enums.window.titleBarLeftMargin
    property string windowTitle: ""
    title: windowTitle  // Sync to native Window.title for taskbar 同步到原生标题用于任务栏显示
    property int windowRadius: Enums.radius.large
    property int shadowSize: Enums.window.qmlShadowSize
    property color windowColor: Enums.backgroundColor
    
    // ==================== Shadow Mode 阴影模式 ====================
    property int shadowMode: Enums.windowShadow.mode_auto
    property bool _dwmInitializationDone: false
    readonly property bool _platformSupportsNative: ShadowManager ? ShadowManager.useNative : false
    readonly property bool _useNativeShadow: {
        if (shadowMode === Enums.windowShadow.mode_none) return false
        if (shadowMode === Enums.windowShadow.mode_native) return true
        if (shadowMode === Enums.windowShadow.mode_qml) return false
        return _platformSupportsNative
    }
    readonly property bool _useQmlShadow: {
        if (shadowMode === Enums.windowShadow.mode_none) return false
        if (shadowMode === Enums.windowShadow.mode_native) return false
        if (shadowMode === Enums.windowShadow.mode_qml) return true
        return !_platformSupportsNative
    }
    
    // ==================== Content Slot 内容插槽 ====================
    default property alias content: contentContainer.data

    // ==================== Left Panel Content Slot 左侧面板内容插槽 ====================
    property alias leftPanelContent: leftPanelContainer.data

    // ==================== Maximized State 最大化状态 ====================
    readonly property bool isMaximized: window.visibility === Window.Maximized
    readonly property int margin: isMaximized ? 0 : (_useNativeShadow ? 0 : (_useQmlShadow ? shadowSize : 0))

    // ==================== Public Methods 公开方法 ====================
    // Public animation methods 公开动画方法
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
        if (window.opacity >= 0.99 && _animOpacity >= 0.99 && _animScale >= 0.99) return
        profileTime("ensureVisiblePaintState " + reason)
        animHelper.restoreVisibleState()
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
    function animatedMinimize() { animHelper.animatedMinimize() }
    function animatedMaximize() { animHelper.animatedMaximize() }
    function animatedRestore() { animHelper.animatedRestore() }

    // ==================== Animation Helper 动画助手 ====================
    WindowAnimationHelper {
        id: animHelper
        targetWindow: window
        onCloseCallback: function() {
            _closeDesktopNotifications()
            var closed = window.close()
            if (closed === false) {
                window._cancelCloseRequest()
            }
        }
        Component.onCompleted: window.profileDetail("WindowAnimationHelper completed")
    }

    // Expose animation properties 暴露动画属性
    property alias _animScale: animHelper.animScale
    property alias _animOpacity: animHelper.animOpacity

    // ==================== Startup Sequence 启动序列 ====================
    Component.onCompleted: {
        profileDetailState("Window root Component.onCompleted pre-init")
        profileTime("Component.onCompleted start; NativeWindow defined=" +
                    (typeof NativeWindow !== "undefined"))
        animHelper.animScale = 0.95
        animHelper.animOpacity = 0
        profileTime("初始化动画状态")
        // 延后 native hook: winId()/style 写入在冷启动可达 90ms+,不要阻塞 loadData。
        // _dwmDelayTimer 中的 finalizeAttach() 会在窗口显示后完成完整 attach。
        _dwmDelayTimer.start()
        profileTime("_dwmDelayTimer.start")
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
        }
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
            NativeWindow.detach(window)
        }
    }
    
    Timer {
        id: _dwmDelayTimer
        interval: 50
        onTriggered: {
            profileTime("_dwmDelayTimer triggered")
            if (_useNativeShadow && ShadowManager) {
                profileTime("ShadowManager.enableShadowForWindow start")
                ShadowManager.enableShadowForWindow(window)
                profileTime("ShadowManager.enableShadowForWindow done")
            }
            // NativeWindowHook 也在此时 attach,winId() 已可用
            if (typeof NativeWindow !== "undefined") {
                profileTime("NativeWindow.finalizeAttach start")
                NativeWindow.finalizeAttach(window)
                profileTime("NativeWindow.finalizeAttach done")
            }
            _dwmInitializationDone = true
            profileTime("DWM initialization marked done")
            // Notify subclasses that DWM-touching ops finished — Mica 等会反复被
            // SWP_FRAMECHANGED 重置的 DWM 属性,必须在此之后才能稳定设置。
            profileTime("nativeHookReady emit start")
            window.nativeHookReady()
            profileTime("nativeHookReady emit done")
            profileTime("animHelper.startShow start")
            animHelper.startShow()
            profileTime("animHelper.startShow done")
        }
    }
    
    // ==================== Shadow Mode Change Handler 阴影模式变化处理 ====================
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
    
    // Listen to ConfigManager signal directly 直接监听ConfigManager信号
    Connections {
        target: typeof ConfigManager !== "undefined" ? ConfigManager : null
        function onDwmShadowChanged() {
            if (!ShadowManager) return
            var enabled = ConfigManager.dwmShadow
            logTime("ConfigManager.dwmShadow changed: " + enabled)
            if (enabled) {
                ShadowManager.enableShadowForWindow(window)
            } else {
                ShadowManager.disableShadowForWindow(window)
            }
        }
    }
    
    Timer {
        id: _animationStartTimer
        interval: 100
        onTriggered: animHelper.startShow()
    }

    Timer {
        id: _resizeHandlesTimer
        interval: 1200
        repeat: false
        onTriggered: {
            _resizeHandlesReady = true
            profileDetail("resize handles ready")
        }
    }

    onVisibilityChanged: {
        animHelper.handleVisibilityChange(window.visibility)
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

    // ==================== Shadow Layer 阴影层 ====================
    Loader {
        id: shadowHost
        anchors.fill: parent
        active: !isMaximized && _useQmlShadow
        visible: active
        opacity: _animOpacity
        scale: _animScale
        asynchronous: true
        source: active ? Qt.resolvedUrl("_internal/QmlShadowHost.qml") : ""
        property var hostWindow: window
        Component.onCompleted: window.profileDetail("shadowHost Loader completed active=" + active + " status=" + status)
        onStatusChanged: window.profileDetail("shadowHost Loader status=" + status + " active=" + active + " source=" + source)
        onLoaded: window.profileDetail("shadowHost Loader loaded")
    }
    
    // ==================== Main Window 主窗口 ====================
    Rectangle {
        id: windowFrame
        anchors.fill: parent
        anchors.margins: margin
        radius: isMaximized ? 0 : windowRadius
        color: windowColor
        opacity: _animOpacity
        scale: _animScale
        clip: true
        Component.onCompleted: window.profileDetail("windowFrame completed margin=" + margin + " radius=" + radius)
        
        // ==================== Top Layout Title Bar 顶部布局标题栏 ====================
        Rectangle {
            id: titleBar
            width: parent.width
            height: _isLeftLayout ? 0 : titleBarHeight
            color: "transparent"
            z: Enums.zIndex.controls
            visible: !_isLeftLayout
            Component.onCompleted: window.profileDetail("titleBar completed visible=" + visible + " height=" + height)
            

            Loader {
                anchors.fill: parent
                active: !_isLeftLayout && _titleChromeReady
                asynchronous: false
                Component.onCompleted: window.profileDetail("titleBar chrome Loader completed active=" + active + " status=" + status)
                onStatusChanged: window.profileDetail("titleBar chrome Loader status=" + status + " active=" + active)
                onLoaded: window.profileDetail("titleBar chrome Loader loaded")
                sourceComponent: Component {
                    Item {
                        anchors.fill: parent
                        Component.onCompleted: window.profileDetail("titleBar chrome content completed")

            WindowIcon {
                id: titleIcon
                x: window.titleBarLeftMargin
                anchors.verticalCenter: parent.verticalCenter
                source: windowIcon
                colored: windowIconColored
                deferLoad: true
                profileTarget: window
                visible: windowIcon !== "" && !_isLeftLayout
                Component.onCompleted: window.profileDetail("titleIcon completed sourceSet=" + (source !== "") + " colored=" + colored)
            }
            
            Text {
                id: titleText
                x: window.titleBarLeftMargin + (titleIcon.visible ? Enums.window.titleIconSize + Enums.window.titleIconGap : 0)
                text: window.windowTitle
                font.family: Enums.fontFamily
                font.pixelSize: Enums.typography.body
                color: Enums.textColor.primary
                anchors.verticalCenter: parent.verticalCenter
                visible: !_isLeftLayout
                Component.onCompleted: window.profileDetail("titleText completed textLength=" + text.length)
            }
            
            Row {
                id: captionButtonsTop
                anchors.right: parent.right
                anchors.top: parent.top
                spacing: Enums.spacing.none
                visible: !_isLeftLayout
                z: Enums.zIndex.controlsAbove  // 确保按钮在拖动区域之上
                Component.onCompleted: window.profileDetail("captionButtonsTop Row completed visible=" + visible)
                
                CaptionButton {
                    targetWindow: window
                    iconType: "minimize"
                    buttonWidth: window.captionButtonWidth
                    buttonHeight: captionButtonHeight
                    onClicked: animatedMinimize()
                    Component.onCompleted: window.profileDetail("captionButton top minimize completed")
                }
                
                CaptionButton {
                    targetWindow: window
                    iconType: isMaximized ? "restore" : "maximize"
                    buttonWidth: window.captionButtonWidth
                    buttonHeight: captionButtonHeight
                    onClicked: isMaximized ? window.showNormal() : window.showMaximized()
                    Component.onCompleted: window.profileDetail("captionButton top max/restore completed iconType=" + iconType)
                }
                
                CaptionButton {
                    targetWindow: window
                    iconType: "close"
                    buttonWidth: window.captionButtonWidth
                    buttonHeight: captionButtonHeight
                    buttonRadius: isMaximized ? 0 : windowRadius
                    onClicked: requestClose()
                    Component.onCompleted: window.profileDetail("captionButton top close completed")
                }
            }
            
            MouseArea {
                anchors.fill: parent
                anchors.rightMargin: captionButtonWidth * 3
                visible: !_isLeftLayout
                z: Enums.zIndex.background  // 确保在按钮之下
                onPressed: (mouse) => { if (!isMaximized) window.startSystemMove() }
                onDoubleClicked: isMaximized ? window.showNormal() : window.showMaximized()
                Component.onCompleted: window.profileDetail("titleBar drag MouseArea completed")
            }
                    }
                }
            }
        }
        
        // ==================== Left Layout Panel 左侧布局面板 ====================
        Rectangle {
            id: leftPanel
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: _isLeftLayout ? Math.max(leftPanelWidth, Enums.window.navPanelMinWidth) : 0
            color: "transparent"
            visible: _isLeftLayout
            z: Enums.zIndex.controls
            Component.onCompleted: window.profileDetail("leftPanel completed visible=" + visible + " width=" + width)
            
            // Left title bar area 左侧标题栏区域
            Rectangle {
                id: leftTitleBar
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: titleBarHeight
                color: "transparent"
                Component.onCompleted: window.profileDetail("leftTitleBar completed")

                Loader {
                    anchors.fill: parent
                    active: _isLeftLayout && _titleChromeReady
                    Component.onCompleted: window.profileDetail("leftTitleBar Loader completed active=" + active + " status=" + status)
                    onStatusChanged: window.profileDetail("leftTitleBar Loader status=" + status + " active=" + active)
                    onLoaded: window.profileDetail("leftTitleBar Loader loaded")
                    sourceComponent: Component {
                        Item {
                            anchors.fill: parent
                            Component.onCompleted: window.profileDetail("leftTitleBar content Item completed")

                            // Window drag area 窗口拖拽区域
                            MouseArea {
                                anchors.fill: parent
                                onPressed: (mouse) => { if (!isMaximized) window.startSystemMove() }
                                onDoubleClicked: isMaximized ? window.showNormal() : window.showMaximized()
                                Component.onCompleted: window.profileDetail("leftTitleBar drag MouseArea completed")
                            }

                            // Window icon 窗口图标
                            WindowIcon {
                                id: leftTitleIcon
                                anchors.left: parent.left
                                anchors.leftMargin: window.titleBarLeftMargin
                                anchors.verticalCenter: parent.verticalCenter
                                source: windowIcon
                                colored: windowIconColored
                                deferLoad: true
                                profileTarget: window
                                Component.onCompleted: window.profileDetail("leftTitleIcon completed sourceSet=" + (source !== ""))
                            }

                            // Window title 窗口标题
                            Text {
                                id: leftTitleText
                                anchors.left: leftTitleIcon.visible ? leftTitleIcon.right : parent.left
                                anchors.leftMargin: leftTitleIcon.visible ? Enums.window.titleIconGap : window.titleBarLeftMargin
                                anchors.verticalCenter: parent.verticalCenter
                                text: window.windowTitle
                                font.family: Enums.fontFamily
                                font.pixelSize: Enums.typography.body
                                color: Enums.textColor.primary
                                Component.onCompleted: window.profileDetail("leftTitleText completed textLength=" + text.length)
                            }
                        }
                    }
                }
            }
            
            // Left panel content container 左侧面板内容容器
            Item {
                id: leftPanelContainer
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: leftTitleBar.bottom
                anchors.bottom: parent.bottom
                Component.onCompleted: window.profileDetail("leftPanelContainer completed")
            }
        }
        
        // ==================== Vertical Divider 垂直分割线 ====================
        Rectangle {
            id: verticalDivider
            anchors.left: leftPanel.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: Enums.border.thin
            color: Enums.stateColor.divider
            visible: _isLeftLayout && _titleChromeReady
            z: Enums.zIndex.controls
            Component.onCompleted: window.profileDetail("verticalDivider completed visible=" + visible)
        }
        
        // ==================== Right Caption Buttons 右侧窗口按钮 ====================
        Item {
            id: captionButtonsRight
            anchors.right: parent.right
            anchors.top: parent.top
            width: _isLeftLayout ? captionButtonWidth * 3 : 0
            height: captionButtonHeight
            visible: _isLeftLayout
            z: Enums.zIndex.controlsAbove
            Component.onCompleted: window.profileDetail("captionButtonsRight host completed visible=" + visible)

            Loader {
                anchors.fill: parent
                active: _isLeftLayout && _titleChromeReady
                Component.onCompleted: window.profileDetail("captionButtonsRight Loader completed active=" + active + " status=" + status)
                onStatusChanged: window.profileDetail("captionButtonsRight Loader status=" + status + " active=" + active)
                onLoaded: window.profileDetail("captionButtonsRight Loader loaded")
                sourceComponent: Component {
                    Row {
                        anchors.fill: parent
                        spacing: Enums.spacing.none
                        Component.onCompleted: window.profileDetail("captionButtonsRight Row completed")

                        CaptionButton {
                            targetWindow: window
                            iconType: "minimize"
                            buttonWidth: window.captionButtonWidth
                            buttonHeight: captionButtonHeight
                            onClicked: animatedMinimize()
                            Component.onCompleted: window.profileDetail("captionButton right minimize completed")
                        }

                        CaptionButton {
                            targetWindow: window
                            iconType: isMaximized ? "restore" : "maximize"
                            buttonWidth: window.captionButtonWidth
                            buttonHeight: captionButtonHeight
                            onClicked: isMaximized ? window.showNormal() : window.showMaximized()
                            Component.onCompleted: window.profileDetail("captionButton right max/restore completed iconType=" + iconType)
                        }

                        CaptionButton {
                            targetWindow: window
                            iconType: "close"
                            buttonWidth: window.captionButtonWidth
                            buttonHeight: captionButtonHeight
                            buttonRadius: isMaximized ? 0 : windowRadius
                            onClicked: requestClose()
                            Component.onCompleted: window.profileDetail("captionButton right close completed")
                        }
                    }
                }
            }
        }
        
        // ==================== Right Title Bar Drag Area 右侧标题栏拖动区域 ====================
        MouseArea {
            id: rightTitleBarDragArea
            anchors.left: verticalDivider.right
            anchors.right: captionButtonsRight.left
            anchors.top: parent.top
            height: titleBarHeight
            visible: _isLeftLayout && _titleChromeReady
            z: Enums.zIndex.controls
            onPressed: (mouse) => { if (!isMaximized) window.startSystemMove() }
            onDoubleClicked: isMaximized ? window.showNormal() : window.showMaximized()
            Component.onCompleted: window.profileDetail("rightTitleBarDragArea completed visible=" + visible)
        }
        
        // ==================== Content Area 内容区域 ====================
        Item {
            id: contentContainer
            objectName: "contentContainer"
            anchors.top: _isLeftLayout ? parent.top : titleBar.bottom
            anchors.left: _isLeftLayout ? verticalDivider.right : parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            Component.onCompleted: window.profileDetail("contentContainer completed dataChildren=" + data.length)
            
            // Click background to clear input focus 点击背景清除输入焦点
            MouseArea {
                anchors.fill: parent
                z: Enums.zIndex.background  // Below all content 在所有内容下方
                onClicked: contentContainer.forceActiveFocus()
                Component.onCompleted: window.profileDetail("contentContainer background MouseArea completed")
            }
        }
        
        // ==================== Border 边框 ====================
        Rectangle {
            anchors.fill: parent
            radius: parent.radius
            color: "transparent"
            border.width: Enums.border.thin
            border.color: Enums.borderColor
            z: Enums.zIndex.controls
            Component.onCompleted: window.profileDetail("window border completed")
        }
    }
    
    // ==================== Resize Handles 调整大小手柄 ====================
    Loader {
        id: resizeHandlesLoader
        anchors.fill: parent
        active: _resizeHandlesReady
        asynchronous: true
        Component.onCompleted: window.profileDetail("resizeHandles Loader completed active=" + active + " status=" + status)
        onStatusChanged: window.profileDetail("resizeHandles Loader status=" + status + " active=" + active)
        onLoaded: window.profileDetail("resizeHandles Loader loaded")
        sourceComponent: Component {
            Item {
                anchors.fill: parent
                Component.onCompleted: window.profileDetail("resizeHandles content completed")
                ResizeArea { targetWindow: window; edge: Qt.LeftEdge; Component.onCompleted: window.profileDetail("ResizeArea left completed") }
                ResizeArea { targetWindow: window; edge: Qt.RightEdge; Component.onCompleted: window.profileDetail("ResizeArea right completed") }
                ResizeArea { targetWindow: window; edge: Qt.TopEdge; Component.onCompleted: window.profileDetail("ResizeArea top completed") }
                ResizeArea { targetWindow: window; edge: Qt.BottomEdge; Component.onCompleted: window.profileDetail("ResizeArea bottom completed") }
            }
        }
    }
}
