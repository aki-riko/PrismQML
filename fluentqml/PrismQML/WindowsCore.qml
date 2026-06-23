// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import QtQuick.Effects
import "effects"
import "./_internal"
import "controls/containers"
import "controls/feedback/Notification"
import "controls/data"

// WindowsCore - Base class for all Window 所有 Window 的基类
// Pure QML: rounded corners + shadow + titlebar + resize 纯QML实现
// Supports top/left title bar layout 支持顶部/左侧标题栏布局
Window {
    id: window
    
    // ==================== Startup Timing 启动计时 ====================
    readonly property real _appStartTime: Date.now()
    function logTime(msg) { console.log("[" + Math.round(Date.now() - _appStartTime) + "ms]", msg) }

    // ==================== Signals 信号 ====================
    // Fired after DWM-touching init done (shadow + native hook attached) 通知子类: DWM 相关初始化完成
    // 子类可挂这个信号设置 Mica 等会被 SWP_FRAMECHANGED 重置的 DWM 属性
    signal nativeHookReady()
    
    // ==================== Window Props 窗口属性 ====================
    width: Enums.window.defaultWidth
    height: Enums.window.defaultHeight
    minimumWidth: Enums.window.minimumWidth
    minimumHeight: Enums.window.minimumHeight
    visible: true
    opacity: Enums.opacityLevel.invisible
    color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint
    
    // ==================== Theme 主题 ====================
    readonly property color accentColor: ThemeManager ? ThemeManager.accentColor : Enums.accentColor
    
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
            WindowHelper.setAppIcon(windowIcon)
        }
    }
    property int titleBarHeight: Enums.window.titleBarHeight
    property int captionButtonHeight: Enums.window.captionButtonHeight
    readonly property int captionButtonWidth: Enums.window.captionButtonWidth
    property int titleBarLeftMargin: Enums.window.titleBarLeftMargin
    property alias windowTitle: titleText.text
    title: windowTitle  // Sync to native Window.title for taskbar 同步到原生标题用于任务栏显示
    property int windowRadius: Enums.radius.large
    property int shadowSize: Enums.window.qmlShadowSize
    property color windowColor: Enums.backgroundColor
    
    // ==================== Shadow Mode 阴影模式 ====================
    property int shadowMode: Enums.windowShadow.mode_auto
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
    function animatedClose() { animHelper.animatedClose() }
    function animatedMinimize() { animHelper.animatedMinimize() }
    function animatedMaximize() { animHelper.animatedMaximize() }
    function animatedRestore() { animHelper.animatedRestore() }

    // ==================== Animation Helper 动画助手 ====================
    WindowAnimationHelper {
        id: animHelper
        targetWindow: window
        onCloseCallback: function() {
            NotificationManager.closeAllDesktopNotifications()
            window.close()
        }
    }

    // Expose animation properties 暴露动画属性
    property alias _animScale: animHelper.animScale
    property alias _animOpacity: animHelper.animOpacity

    // ==================== Startup Sequence 启动序列 ====================
    Component.onCompleted: {
        console.log("[WindowsCore] Component.onCompleted, NativeWindow defined:",
                    typeof NativeWindow !== "undefined")
        animHelper.animScale = 0.95
        animHelper.animOpacity = 0
        // 直接尝试 attach: 多数情况 winId() 此时已可用; 失败也无副作用 (内部静默 return)
        if (typeof NativeWindow !== "undefined") {
            NativeWindow.attach(window)
        }
        _dwmDelayTimer.start()
    }

    onClosing: {
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
            if (_useNativeShadow && ShadowManager) {
                logTime("DWM shadow enabled")
                ShadowManager.enableShadowForWindow(window)
            }
            // NativeWindowHook 也在此时 attach,winId() 已可用
            if (typeof NativeWindow !== "undefined") {
                logTime("NativeWindow.attach")
                NativeWindow.attach(window)
            }
            // Notify subclasses that DWM-touching ops finished — Mica 等会反复被
            // SWP_FRAMECHANGED 重置的 DWM 属性,必须在此之后才能稳定设置。
            window.nativeHookReady()
            animHelper.startShow()
        }
    }
    
    // ==================== Shadow Mode Change Handler 阴影模式变化处理 ====================
    on_UseNativeShadowChanged: {
        if (!ShadowManager) return
        if (_useNativeShadow) {
            logTime("DWM shadow enabled (runtime)")
            ShadowManager.enableShadowForWindow(window)
        } else {
            logTime("DWM shadow disabled (runtime)")
            ShadowManager.disableShadowForWindow(window)
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

    onVisibilityChanged: animHelper.handleVisibilityChange(window.visibility)

    // 从隐藏恢复显示时重新播放显示动画,把 opacity 拉回 1。
    // 背景: 窗口 opacity 初值为 0(invisible),靠 startShow() 动画拉到 1;
    // 关闭动画 closeAnim 会把 opacity 设回 0。下游"隐藏到托盘"再调裸 show()
    // 恢复时,opacity 仍停在 0 → layered 窗口 alpha=0 完全透明 → 窗口"打开了"
    // 却完全看不见(实测 GetLayeredWindowAttributes alpha=0)。这里在 visible
    // 由 false→true 且 opacity 仍接近 0 时自动补一次 startShow,使所有下游
    // (含直接调 QWindow.show() 的)无需改调用方即可正确恢复显示。
    // 守卫 opacity < 0.5: 避免与正常启动序列(startShow 已在跑)/最大化还原
    //   (opacity 已是 1)重复触发动画。
    onVisibleChanged: {
        if (window.visible && window.opacity < 0.5) {
            animHelper.startShow()
        }
    }

    // ==================== Shadow Layer 阴影层 ====================
    Item {
        id: shadowHost
        anchors.fill: parent
        visible: !isMaximized && _useQmlShadow
        opacity: _animOpacity
        scale: _animScale
        
        RectangularShadow {
            anchors.fill: shadowSource
            radius: shadowSource.radius
            color: Enums.shadow.level28.color
            blur: Enums.shadow.level28.blur
            offset: Qt.vector2d(0, Enums.shadow.level28.offset)
        }
        
        Rectangle {
            id: shadowSource
            anchors.centerIn: parent
            width: parent.width - shadowSize * 2
            height: parent.height - shadowSize * 2
            radius: windowRadius
            color: windowColor
        }
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
        
        // ==================== Top Layout Title Bar 顶部布局标题栏 ====================
        Rectangle {
            id: titleBar
            width: parent.width
            height: _isLeftLayout ? 0 : titleBarHeight
            color: "transparent"
            z: Enums.zIndex.controls
            visible: !_isLeftLayout
            

            WindowIcon {
                id: titleIcon
                x: window.titleBarLeftMargin
                anchors.verticalCenter: parent.verticalCenter
                source: windowIcon
                colored: windowIconColored
                visible: windowIcon !== "" && !_isLeftLayout
            }
            
            Label {
                id: titleText
                x: window.titleBarLeftMargin + (titleIcon.visible ? Enums.window.titleIconSize + Enums.window.titleIconGap : 0)
                type: Enums.label.type_body
                color: Enums.textColor.primary
                anchors.verticalCenter: parent.verticalCenter
                visible: !_isLeftLayout
            }
            
            Row {
                id: captionButtonsTop
                anchors.right: parent.right
                anchors.top: parent.top
                spacing: Enums.spacing.none
                visible: !_isLeftLayout
                z: Enums.zIndex.controlsAbove  // 确保按钮在拖动区域之上
                
                CaptionButton {
                    targetWindow: window
                    iconType: "minimize"
                    buttonWidth: window.captionButtonWidth
                    buttonHeight: captionButtonHeight
                    onClicked: animatedMinimize()
                }
                
                CaptionButton {
                    targetWindow: window
                    iconType: isMaximized ? "restore" : "maximize"
                    buttonWidth: window.captionButtonWidth
                    buttonHeight: captionButtonHeight
                    onClicked: isMaximized ? window.showNormal() : window.showMaximized()
                }
                
                Rectangle {
                    width: window.captionButtonWidth
                    height: captionButtonHeight
                    radius: isMaximized ? 0 : windowRadius
                    color: closeAreaTop.pressed ? Enums.windowButtonColors.closePressed : (closeAreaTop.containsMouse ? Enums.windowButtonColors.closeHover : "transparent")
                    
                    Rectangle {
                        anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
                        width: parent.radius; color: parent.color; visible: parent.radius > 0
                    }
                    Rectangle {
                        anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
                        height: parent.radius; color: parent.color; visible: parent.radius > 0
                    }
                    
                    Canvas {
                        anchors.centerIn: parent
                        width: Enums.window.captionIconSize
                        height: Enums.window.captionIconSize
                        readonly property color iconColor: closeAreaTop.containsMouse ? Enums.windowButtonColors.iconLight : (Enums.isDark ? Enums.windowButtonColors.iconLight : Enums.windowButtonColors.iconDark)
                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.clearRect(0, 0, width, height)
                            ctx.strokeStyle = iconColor; ctx.lineWidth = 1
                            ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(width, height)
                            ctx.moveTo(width, 0); ctx.lineTo(0, height); ctx.stroke()
                        }
                        onIconColorChanged: requestPaint()
                        Component.onCompleted: requestPaint()
                    }
                    
                    MouseArea {
                        id: closeAreaTop
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: animatedClose()
                    }
                }
            }
            
            MouseArea {
                anchors.fill: parent
                anchors.rightMargin: captionButtonWidth * 3
                visible: !_isLeftLayout
                z: Enums.zIndex.background  // 确保在按钮之下
                onPressed: (mouse) => { if (!isMaximized) window.startSystemMove() }
                onDoubleClicked: isMaximized ? window.showNormal() : window.showMaximized()
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
            
            // Left title bar area 左侧标题栏区域
            Rectangle {
                id: leftTitleBar
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: titleBarHeight
                color: "transparent"
                
                // Window drag area 窗口拖拽区域
                MouseArea {
                    anchors.fill: parent
                    onPressed: (mouse) => { if (!isMaximized) window.startSystemMove() }
                    onDoubleClicked: isMaximized ? window.showNormal() : window.showMaximized()
                }
                
                // Window icon 窗口图标
                WindowIcon {
                    id: leftTitleIcon
                    anchors.left: parent.left
                    anchors.leftMargin: window.titleBarLeftMargin
                    anchors.verticalCenter: parent.verticalCenter
                    source: windowIcon
                    colored: windowIconColored
                }
                
                // Window title 窗口标题
                Label {
                    id: leftTitleText
                    anchors.left: leftTitleIcon.visible ? leftTitleIcon.right : parent.left
                    anchors.leftMargin: leftTitleIcon.visible ? Enums.window.titleIconGap : window.titleBarLeftMargin
                    anchors.verticalCenter: parent.verticalCenter
                    text: window.windowTitle
                    type: Enums.label.type_body
                    color: Enums.textColor.primary
                }
            }
            
            // Left panel content container 左侧面板内容容器
            Item {
                id: leftPanelContainer
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: leftTitleBar.bottom
                anchors.bottom: parent.bottom
            }
        }
        
        // ==================== Vertical Divider 垂直分割线 ====================
        Separator {
            id: verticalDivider
            type: Enums.separator.vertical
            anchors.left: leftPanel.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            visible: _isLeftLayout
            z: Enums.zIndex.controls
        }
        
        // ==================== Right Caption Buttons 右侧窗口按钮 ====================
        Row {
            id: captionButtonsRight
            anchors.right: parent.right
            anchors.top: parent.top
            spacing: Enums.spacing.none
            visible: _isLeftLayout
            z: Enums.zIndex.controlsAbove
            
            CaptionButton {
                targetWindow: window
                iconType: "minimize"
                buttonWidth: window.captionButtonWidth
                buttonHeight: captionButtonHeight
                onClicked: animatedMinimize()
            }
            
            CaptionButton {
                targetWindow: window
                iconType: isMaximized ? "restore" : "maximize"
                buttonWidth: window.captionButtonWidth
                buttonHeight: captionButtonHeight
                onClicked: isMaximized ? window.showNormal() : window.showMaximized()
            }
            
            Rectangle {
                width: window.captionButtonWidth
                height: captionButtonHeight
                radius: isMaximized ? 0 : windowRadius
                color: closeAreaRight.pressed ? Enums.windowButtonColors.closePressed : (closeAreaRight.containsMouse ? Enums.windowButtonColors.closeHover : "transparent")
                
                Rectangle {
                    anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
                    width: parent.radius; color: parent.color; visible: parent.radius > 0
                }
                Rectangle {
                    anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
                    height: parent.radius; color: parent.color; visible: parent.radius > 0
                }
                
                Canvas {
                    anchors.centerIn: parent
                    width: Enums.window.captionIconSize
                    height: Enums.window.captionIconSize
                    readonly property color iconColor: closeAreaRight.containsMouse ? Enums.windowButtonColors.iconLight : (Enums.isDark ? Enums.windowButtonColors.iconLight : Enums.windowButtonColors.iconDark)
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        ctx.strokeStyle = iconColor; ctx.lineWidth = 1
                        ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(width, height)
                        ctx.moveTo(width, 0); ctx.lineTo(0, height); ctx.stroke()
                    }
                    onIconColorChanged: requestPaint()
                    Component.onCompleted: requestPaint()
                }
                
                MouseArea {
                    id: closeAreaRight
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: animatedClose()
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
            visible: _isLeftLayout
            z: Enums.zIndex.controls
            onPressed: (mouse) => { if (!isMaximized) window.startSystemMove() }
            onDoubleClicked: isMaximized ? window.showNormal() : window.showMaximized()
        }
        
        // ==================== Content Area 内容区域 ====================
        Item {
            id: contentContainer
            objectName: "contentContainer"
            anchors.top: _isLeftLayout ? parent.top : titleBar.bottom
            anchors.left: _isLeftLayout ? verticalDivider.right : parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            
            // Click background to clear input focus 点击背景清除输入焦点
            MouseArea {
                anchors.fill: parent
                z: Enums.zIndex.background  // Below all content 在所有内容下方
                onClicked: contentContainer.forceActiveFocus()
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
        }
    }
    
    // ==================== Resize Handles 调整大小手柄 ====================
    ResizeArea { targetWindow: window; edge: Qt.LeftEdge }
    ResizeArea { targetWindow: window; edge: Qt.RightEdge }
    ResizeArea { targetWindow: window; edge: Qt.TopEdge }
    ResizeArea { targetWindow: window; edge: Qt.BottomEdge }
}
