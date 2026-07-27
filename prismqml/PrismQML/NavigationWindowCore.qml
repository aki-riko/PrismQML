// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import "navigation"
import "controls/navigation"
import "controls/feedback/SplashScreen"

// NavigationWindowCore - Base class for navigation windows 导航窗口基类
// Provides common navigation logic for all navigation windows 为所有导航窗口提供公共导航逻辑
WindowsCore {
    id: window

    // ==================== Public Props 公开属性 ====================
    property var navigationItems: []
    property var bottomNavigationItems: []
    property int currentIndex: 0
    // Navigation bar reference; subclasses must override it. 导航栏引用，由子类覆盖。
    property var navigationView: null
    // Page container reference; subclasses set it when ready. 页面容器引用，由子类在就绪后设置。
    property var stackedWidget: null
    property bool navigationSmoothScroll: true
    property int navigationScrollDuration: Enums.duration.navigationScroll
    property real navigationScrollStep: Enums.spacing.navigationScrollStep
    property bool micaEnabled: false
    property bool lazyLoading: false
    property string loadingText: Translator.tr("loading")
    property bool splashEnabled: true  // Enable the shared startup overlay 启用通用启动覆盖层
    property string splashIcon: ""  // Empty inherits windowIcon 空值继承窗口图标
    property string splashTitle: ""  // Empty inherits windowTitle 空值继承窗口标题
    property string splashSubtitle: ""  // Startup status text 启动状态文本
    property int splashMinimumVisibleDuration: Enums.duration.splashMinimumVisible  // Stable display after window exposure 窗口可见后的最短稳定展示时长
    // Replaceable startup visual; the root must provide finish(). 可替换启动视觉，根对象须提供 finish()。
    property Component splashComponent: Component {
        SplashScreen {
            iconSource: window.splashIcon !== "" ? window.splashIcon : window.windowIcon
            title: window.splashTitle !== "" ? window.splashTitle : window.windowTitle
            subtitle: window.splashSubtitle
        }
    }

    // ==================== Internal Props 内部属性 ====================
    // Splash instance owned by the shared loader. 由通用加载器持有的欢迎页实例。
    property var _splashInstance: null
    property bool _micaBackdropReady: false
    property bool _pythonLoading: false
    property int _pythonPendingIndex: -1
    property bool _pythonPageMode: false
    property bool _nativeHookReady: false
    property string _micaReapplyReason: ""
    property bool _splashDismissed: false
    property bool _splashDismissRequested: false
    property double _splashVisibleSinceMs: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _micaAvailable: MicaManager ? MicaManager.isMicaSupported : false
    // Neo uses an opaque surface and hard shadow, so Mica must stay disabled. Neo 使用实色表面与硬阴影，因此必须关闭 Mica。
    readonly property bool _micaActive: micaEnabled && _micaAvailable && !Enums.isNeobrutalism
    readonly property bool _micaTransparent: _micaActive && _micaBackdropReady
    readonly property color contentBgColor: _micaTransparent
        ? Enums.stateColor.contentBgTransparent
        : Enums.stateColor.contentBg
    readonly property int contentCornerRadius: Enums.radius.large
    readonly property var _safeNavigationItems:
        navigationItems === null || navigationItems === undefined ? []
        : (typeof navigationItems.length === "number" ? navigationItems : [])
    readonly property var _safeBottomNavigationItems:
        bottomNavigationItems === null || bottomNavigationItems === undefined ? []
        : (typeof bottomNavigationItems.length === "number" ? bottomNavigationItems : [])

    // ==================== Signals 信号 ====================
    signal pythonPageReady(int index)
    signal bottomItemClicked(int index)
    signal currentPageChanged(int index)

    // ==================== Internal Methods 内部方法 ====================
    function _startPythonLoading(index) {
        _pythonPendingIndex = index
        _pythonLoading = true
    }

    function _finishPythonLoading() {
        _pythonLoading = false
        var idx = _pythonPendingIndex
        _pythonPendingIndex = -1
        if (stackedWidget && idx >= 0) {
            stackedWidget._completePythonLazySwitch(idx)
        }
        pythonPageReady(idx)
    }

    function _markPythonPageReady(index) {
        if (stackedWidget && stackedWidget._markPythonPageReady) {
            stackedWidget._markPythonPageReady(index)
        }
    }

    function _applyMicaEffect(reason) {
        if (!MicaManager || !_micaAvailable || !_nativeHookReady) {
            _micaBackdropReady = false
            return false
        }
        profileTime("NavigationWindowCore apply Mica " + reason + " start")
        var success = MicaManager.setMicaEffect(window, _micaActive, Enums.isDark)
        _micaBackdropReady = _micaActive && success
        profileTime("NavigationWindowCore apply Mica " + reason + " done success=" + success)
        return success
    }

    function _scheduleMicaReapply(reason) {
        if (!_micaActive || !_nativeHookReady) return
        // Hide the transparent fallback until DWM confirms the backdrop again.
        // 在 DWM 重新确认背板前关闭透明兜底，避免只剩透明外壳。
        _micaBackdropReady = false
        _micaReapplyReason = reason
        _micaReapplyTimer.restart()
        _micaLateReapplyTimer.restart()
    }

    function _moveDefaultPage(child, container, pageIndex, sourceIndex, ownerName) {
        if (!child || !(child instanceof Item)) {
            console.warn(
                "[" + ownerName + "] Skipping non-Item default child / " +
                "跳过非 Item 默认子对象: sourceIndex=" + sourceIndex
            )
            return false
        }

        try {
            child.parent = container
            child.width = Qt.binding(function() { return container.width })
            child.height = Qt.binding(function() { return container.height })
            child.x = 0
            child.y = 0
            child.scale = 1
            child.visible = (pageIndex === stackedWidget.currentIndex)
            child.opacity = (pageIndex === stackedWidget.currentIndex ? 1 : 0)
            return true
        } catch (error) {
            console.warn(
                "[" + ownerName + "] Failed to move default page / " +
                "迁移默认页面失败: sourceIndex=" + sourceIndex + ", error=" + error
            )
            return false
        }
    }

    function _moveDefaultPages(stagedItems, container, ownerName) {
        var items = []
        for (var i = 0; i < stagedItems.length; i++) {
            items.push(stagedItems[i])
        }

        var pageIndex = 0
        for (var sourceIndex = 0; sourceIndex < items.length; sourceIndex++) {
            if (_moveDefaultPage(
                items[sourceIndex], container, pageIndex, sourceIndex, ownerName
            )) {
                pageIndex += 1
            }
        }
        return pageIndex
    }

    function _dismissSplashWhenReady(stack) {
        profileTime("NavigationWindowCore _dismissSplashWhenReady start")
        if (_splashDismissed) {
            profileTime("NavigationWindowCore splash already dismissed")
            return
        }
        if (!_splashInstance) {
            _splashDismissed = true
            profileTime("NavigationWindowCore no splash instance")
            return
        }

        // Dismiss immediately when the current page is already loaded. 当前页已加载时立即关闭欢迎页。
        if (!stack || stack._isPageLoaded(stack.currentIndex)) {
            profileTime("NavigationWindowCore splash ready immediate")
            _requestSplashDismiss()
            return
        }

        // Otherwise wait for the current page, with a timeout fallback. 否则等待当前页，并保留超时兜底。
        var target = stack.currentIndex
        function onPageLoaded(idx) {
            if (idx !== target) return
            stack.pageLoaded.disconnect(onPageLoaded)
            _splashTimeoutTimer.stop()
            profileTime("NavigationWindowCore splash pageLoaded target=" + idx)
            _requestSplashDismiss()
        }
        stack.pageLoaded.connect(onPageLoaded)
        _splashTimeoutTimer._onTimeout = function() {
            stack.pageLoaded.disconnect(onPageLoaded)
            profileTime("NavigationWindowCore splash timeout")
            _requestSplashDismiss()
        }
        _splashTimeoutTimer.restart()
        profileTime("NavigationWindowCore splash wait pageLoaded target=" + target)
    }

    function _markSplashVisible() {
        if (_splashVisibleSinceMs > 0 || !_splashInstance || !window.visible) return
        _splashVisibleSinceMs = Date.now()
        profileTime("NavigationWindowCore splash visible")
        _scheduleSplashDismiss()
    }

    function _requestSplashDismiss() {
        if (_splashDismissed) return
        _splashDismissRequested = true
        _scheduleSplashDismiss()
    }

    function _scheduleSplashDismiss() {
        if (_splashDismissed || !_splashDismissRequested) return
        if (_splashVisibleSinceMs <= 0) {
            profileTime("NavigationWindowCore splash wait visible")
            return
        }

        var elapsed = Date.now() - _splashVisibleSinceMs
        var remaining = Math.max(0, splashMinimumVisibleDuration - elapsed)
        if (remaining > 0) {
            _splashMinimumVisibleTimer.interval = Math.max(Enums.duration.tick, Math.ceil(remaining))
            _splashMinimumVisibleTimer.restart()
            profileTime("NavigationWindowCore splash wait minimum visible remaining=" + Math.ceil(remaining))
            return
        }
        _doDismissSplash()
    }

    function _doDismissSplash() {
        if (_splashDismissed) {
            profileTime("NavigationWindowCore _doDismissSplash skipped")
            return
        }
        _splashDismissed = true
        _splashMinimumVisibleTimer.stop()
        profileTime("NavigationWindowCore splash finish start")
        if (_splashInstance) _splashInstance.finish()
        profileTime("NavigationWindowCore splash finish done")
    }

    function _handleBottomItemClicked(index, navPanel, stack, pageSources) {
        var item = _safeBottomNavigationItems[index]
        var isPageItem = item && item.key !== undefined
        var isSelectable = item && item.selectable !== false
        var safePageSources = pageSources && typeof pageSources.length === "number"
            ? pageSources : []

        if (!isPageItem || !isSelectable) {
            // Function items only emit the public signal. 功能项只发送公开信号。
            bottomItemClicked(index)
            return -1
        }

        var pageIndex = -1
        // Prefer the Python window key format page_N. 优先解析 Python 窗口的 page_N 键格式。
        var itemKey = String(item.key)
        var match = itemKey.match(/^page_(\d+)$/)
        if (match) {
            pageIndex = parseInt(match[1])
        } else {
            // Otherwise search QML lazy-loading sources. 否则搜索 QML 懒加载源。
            for (var i = 0; i < safePageSources.length; i++) {
                var source = safePageSources[i]
                if (source === null || source === undefined) continue
                if (String(source).indexOf(itemKey) !== -1) {
                    pageIndex = i
                    break
                }
            }
        }

        if (pageIndex >= 0) {
            var oldMap = navPanel._bottomPageIndexMap || {}
            var map = ({})
            for (var k in oldMap) { map[k] = oldMap[k] }
            map[item.key] = pageIndex
            navPanel._bottomPageIndexMap = map

            // Change the window source index only; direct stack writes would break its binding.
            // 只修改窗口源索引；直接写 stack 会破坏其声明式绑定。
            // Suppress the top-item indicator path so the bottom item owns this animation.
            // 暂停顶部项指示器路径，让底部项独占本次动画。
            navPanel._skipIndicatorAnimation = true
            currentIndex = pageIndex
            navPanel._skipIndicatorAnimation = false
            currentPageChanged(pageIndex)
            navPanel.updateIndicatorForBottomItem(item.key)
        }
        bottomItemClicked(index)
        return pageIndex
    }

    // ==================== Public Methods 公开方法 ====================
    function setMicaEffectEnabled(enabled) {
        micaEnabled = enabled
        if (!_micaAvailable) {
            _micaBackdropReady = false
            console.log("[NavigationWindowCore] Mica not available")
            return false
        }
        return _applyMicaEffect("setMicaEffectEnabled")
    }

    function isMicaEffectEnabled() { return _micaTransparent }

    function setLanguage(lang) {
        Translator.setLanguage(lang)
    }

    function getLanguage() {
        return Translator.language
    }

    function addPage(page, icon, text, selectedIcon, position, parent, isTransparent) {
        var pos = position || "top"
        var navItem = {
            "icon": icon || "",
            "text": text || "",
            "selectedIcon": selectedIcon || icon || "",
            "key": text || ("page_" + _safeNavigationItems.length),
            "parentKey": parent || "",
            "isTransparent": isTransparent || false
        }

        if (pos === "bottom") {
            var bottomItems = _safeBottomNavigationItems.slice()
            bottomItems.push(navItem)
            bottomNavigationItems = bottomItems
        } else {
            var items = _safeNavigationItems.slice()
            items.push(navItem)
            navigationItems = items
        }

        return navItem
    }

    function removePage(keyOrIndex) {
        var idx = typeof keyOrIndex === "number" ? keyOrIndex : findKeyIndex(keyOrIndex)
        if (idx >= 0 && idx < _safeNavigationItems.length) {
            var items = _safeNavigationItems.slice()
            items.splice(idx, 1)
            navigationItems = items
        }
    }

    function navigateTo(indexOrKey) {
        var idx = typeof indexOrKey === "number" ? indexOrKey : findKeyIndex(indexOrKey)
        if (idx >= 0) {
            // Update the source index once; child bindings follow it automatically.
            // 只更新一次源索引，子组件通过绑定自动跟随。
            currentIndex = idx
        }
    }

    function setCurrentItem(key) { navigateTo(key) }

    function findKeyIndex(key) {
        for (var i = 0; i < _safeNavigationItems.length; i++) {
            var item = _safeNavigationItems[i]
            if (item && (item.key === key || item.text === key)) return i
        }
        return -1
    }

    windowColor: _micaTransparent ? Enums.transparent : Enums.backgroundColor

    Component.onCompleted: {
        profileDetail(
            "NavigationWindowCore completed micaAvailable=" + _micaAvailable +
            " micaEnabled=" + micaEnabled +
            " nav=" + _safeNavigationItems.length +
            " bottom=" + _safeBottomNavigationItems.length
        )
        _markSplashVisible()
    }

    onMicaEnabledChanged: {
        if (_micaAvailable && MicaManager && _nativeHookReady) {
            _applyMicaEffect("micaEnabledChanged")
        } else {
            _micaBackdropReady = false
        }
    }

    onVisibleChanged: {
        if (visible) {
            _markSplashVisible()
            _scheduleMicaReapply("visibleChanged")
        }
        else _micaBackdropReady = false
    }

    onVisibilityChanged: {
        if (window.visibility !== Window.Hidden && window.visibility !== Window.Minimized) {
            _scheduleMicaReapply("visibilityChanged")
        }
    }

    onActiveChanged: {
        if (active) _scheduleMicaReapply("activeChanged")
    }

    // Apply Mica only after the native hook completes its frame changes.
    // 仅在原生钩子完成窗口框架变更后应用 Mica，避免 DWM 背板被重置。
    onNativeHookReady: {
        if (!_micaAvailable) return
        profileTime("NavigationWindowCore nativeHookReady handler start")
        _nativeHookReady = true
        _applyMicaEffect("nativeHookReady")
        profileTime("NavigationWindowCore nativeHookReady handler done")
    }

    // ==================== Content 内容 ====================
    Loader {
        id: _splashLoader

        objectName: "windowSplashLoader"
        parent: window.contentItem
        anchors.fill: parent
        z: Enums.zIndex.splash
        active: window.splashEnabled
        sourceComponent: window.splashComponent
        onItemChanged: {
            window._splashInstance = item
            if (item) {
                window.profileTime("NavigationWindowCore splash mounted")
                window._markSplashVisible()
            }
        }
    }

    Timer {
        id: _splashMinimumVisibleTimer

        interval: Enums.duration.splashMinimumVisible
        onTriggered: window._scheduleSplashDismiss()
    }

    Timer {
        id: _splashTimeoutTimer
        property var _onTimeout: null

        interval: Enums.duration.splashTimeout
        onTriggered: if (_onTimeout) _onTimeout()
    }

    Timer {
        id: _micaReapplyTimer

        interval: Enums.window.micaReapplyDelayMs
        onTriggered: window._applyMicaEffect("restore:" + window._micaReapplyReason)
    }

    Timer {
        id: _micaLateReapplyTimer

        interval: Enums.window.micaLateReapplyDelayMs
        onTriggered: window._applyMicaEffect("late-restore:" + window._micaReapplyReason)
    }

    // Keep ConfigManager changes as a fallback when a property binding is bypassed.
    // 当外部绕过属性绑定时，使用 ConfigManager 信号作为兜底。
    Connections {
        function onMicaEnabledChanged() {
            if (window._micaAvailable && MicaManager && window._nativeHookReady) {
                window.micaEnabled = ConfigManager.micaEnabled
                window._applyMicaEffect("configChanged")
            } else {
                window._micaBackdropReady = false
            }
        }

        target: typeof ConfigManager !== "undefined" ? ConfigManager : null
    }

    Connections {
        function onIsDarkChanged() {
            if (window._micaActive && MicaManager) window._scheduleMicaReapply("themeChanged")
        }
        function onIsNeobrutalismChanged() {
            if (MicaManager) window._applyMicaEffect("skinChanged")
        }

        target: Enums
        enabled: window._micaAvailable && window._nativeHookReady
    }
}
