// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "navigation"
import "controls/navigation"

// NavigationWindowCore - Base class for navigation windows 导航窗口基类
// Provides common navigation logic for all navigation windows 为所有导航窗口提供公共导航逻辑
WindowsCore {
    id: window
    
    // ==================== Navigation Props 导航属性 ====================
    property var navigationItems: []
    property var bottomNavigationItems: []
    property int currentIndex: 0
    
    // Navigation bar reference (subclass must override) 导航栏引用（子类必须覆盖）
    property var navigationView: null
    
    // Page container reference (subclass must set) 页面容器引用（子类必须设置）
    property var stackedWidget: null
    
    // Splash screen instance reference (set by caller, dismissed on content ready) 启动屏幕实例引用
    property var _splashInstance: null
    
    // ==================== Mica Effect 云母效果 ====================
    property bool micaEnabled: false
    readonly property bool _micaAvailable: MicaManager ? MicaManager.isWin11 : false
    // neo 皮肤强制关 Mica: neo 是实心米白底+硬阴影的扁平风, Mica 半透明模糊与之冲突
    readonly property bool _micaActive: micaEnabled && _micaAvailable && !Enums.isNeobrutalism
    windowColor: _micaActive ? Enums.transparent : Enums.backgroundColor
    
    // ==================== Content Area Props 内容区域属性 ====================
    readonly property color contentBgColor: _micaActive ? Enums.stateColor.contentBgTransparent : Enums.stateColor.contentBg
    readonly property int contentCornerRadius: Enums.radius.large
    
    // ==================== Lazy Loading 懒加载 ====================
    property bool lazyLoading: false
    property string loadingText: Translator.tr("loading")
    
    // ==================== Python Lazy Loading Support Python懒加载支持 ====================
    property bool _pythonLoading: false
    property int _pythonPendingIndex: -1
    
    signal pythonPageReady(int index)
    
    function _startPythonLoading(index) {
        _pythonPendingIndex = index
        _pythonLoading = true
    }
    
    function _finishPythonLoading() {
        _pythonLoading = false
        var idx = _pythonPendingIndex
        _pythonPendingIndex = -1
        pythonPageReady(idx)
    }
    
    // ==================== Mica Methods 云母方法 ====================
    function setMicaEffectEnabled(enabled) {
        if (!_micaAvailable) {
            console.log("[NavigationWindowCore] Mica not available")
            return false
        }
        micaEnabled = enabled
        return MicaManager.setMicaEffect(window, enabled, Enums.isDark)
    }
    function isMicaEffectEnabled() { return _micaActive }
    
    // ==================== Language Methods 语言方法 ====================
    function setLanguage(lang) {
        Translator.setLanguage(lang)
    }
    function getLanguage() {
        return Translator.language
    }
    
    // 在 nativeHookReady 触发前的 setMicaEffect 都会被 SWP_FRAMECHANGED 清,徒劳。
    // 这个守卫让早期调用直接跳过,等 hook 完成后由 nativeHookReady 一次性 apply 当前状态。
    property bool _nativeHookReady: false

    // ==================== Signals 信号 ====================
    signal bottomItemClicked(int index)
    signal currentPageChanged(int index)

    // ==================== Splash 关闭时机 ====================
    // 关闭欢迎页必须等"主页(首屏 currentIndex 那一页)真正加载完成",
    // 而非外层框架壳 onLoaded 就关 —— 懒加载/异步模式下框架 ready 时
    // 主页内容仍在异步加载, 过早关 splash 会露出空白再浮现主页。
    property bool _splashDismissed: false

    function _dismissSplashWhenReady(stack) {
        if (_splashDismissed) return
        if (!_splashInstance) { _splashDismissed = true; return }

        // 主页此刻已就绪(同步/直接 children 模式, 或加载够快) → 立即关
        if (!stack || stack._isPageLoaded(stack.currentIndex)) {
            _doDismissSplash()
            return
        }

        // 否则等主页那一页的 pageLoaded 信号; 超时兜底防信号意外不来卡死
        var target = stack.currentIndex
        function onPageLoaded(idx) {
            if (idx !== target) return
            stack.pageLoaded.disconnect(onPageLoaded)
            _splashTimeoutTimer.stop()
            _doDismissSplash()
        }
        stack.pageLoaded.connect(onPageLoaded)
        _splashTimeoutTimer._onTimeout = function() {
            stack.pageLoaded.disconnect(onPageLoaded)
            _doDismissSplash()
        }
        _splashTimeoutTimer.restart()
    }

    function _doDismissSplash() {
        if (_splashDismissed) return
        _splashDismissed = true
        if (_splashInstance) _splashInstance.finish()
    }

    Timer {
        id: _splashTimeoutTimer
        interval: Enums.duration.splashTimeout
        property var _onTimeout: null
        onTriggered: if (_onTimeout) _onTimeout()
    }

    // ==================== Public Methods 公开方法 ====================
    function addPage(page, icon, text, selectedIcon, position, parent, isTransparent) {
        var pos = position || "top"
        var navItem = {
            "icon": icon || "",
            "text": text || "",
            "selectedIcon": selectedIcon || icon || "",
            "key": text || ("page_" + navigationItems.length),
            "parentKey": parent || "",
            "isTransparent": isTransparent || false
        }

        if (pos === "bottom") {
            var bottomItems = bottomNavigationItems.slice()
            bottomItems.push(navItem)
            bottomNavigationItems = bottomItems
        } else {
            var items = navigationItems.slice()
            items.push(navItem)
            navigationItems = items
        }

        return navItem
    }

    function removePage(keyOrIndex) {
        var idx = typeof keyOrIndex === "number" ? keyOrIndex : findKeyIndex(keyOrIndex)
        if (idx >= 0 && idx < navigationItems.length) {
            var items = navigationItems.slice()
            items.splice(idx, 1)
            navigationItems = items
        }
    }

    function navigateTo(indexOrKey) {
        var idx = typeof indexOrKey === "number" ? indexOrKey : findKeyIndex(indexOrKey)
        if (idx >= 0) {
            // 只改 currentIndex 一处, 子内部 (navigationBar / stackedWidget)
            // 通过 Qt Binding 自动跟随,避免之前手动三处赋值任一处失败导致失同步
            currentIndex = idx
        }
    }

    function setCurrentItem(key) { navigateTo(key) }

    function findKeyIndex(key) {
        for (var i = 0; i < navigationItems.length; i++) {
            if (navigationItems[i].key === key || navigationItems[i].text === key) return i
        }
        return -1
    }

    // ==================== 公共 bottomItemClicked 处理 Common Bottom Item Handler ====================
    // 提取自 WindowsBar/Split/Filled 中重复的 onBottomItemClicked 逻辑
    function _handleBottomItemClicked(index, navPanel, stack, pageSources) {
        var item = bottomNavigationItems[index]
        var isPageItem = item && item.key !== undefined
        var isSelectable = item && item.selectable !== false

        if (!isPageItem || !isSelectable) {
            // Function item, only emit signal 功能项，仅发送信号
            bottomItemClicked(index)
            return -1  // 表示无需切换页面
        }

        // Page item: find page index by key 页面项：通过key查找页面索引
        var pageIndex = -1

        // Method 1: Extract index from key format "page_N" (Python window style)
        var match = item.key.match(/^page_(\d+)$/)
        if (match) {
            pageIndex = parseInt(match[1])
        } else if (pageSources) {
            // Method 2: Search in pageSources (QML lazy loading style)
            for (var i = 0; i < pageSources.length; i++) {
                var source = pageSources[i].toString()
                if (source.indexOf(item.key) !== -1) {
                    pageIndex = i
                    break
                }
            }
        }

        if (pageIndex >= 0) {
            // Update bottom page index map for correct selection state
            var oldMap = navPanel._bottomPageIndexMap || {}
            var map = ({})
            for (var k in oldMap) { map[k] = oldMap[k] }
            map[item.key] = pageIndex
            navPanel._bottomPageIndexMap = map

            // ⚠️ 不再 stack.currentIndex = pageIndex — 三种 Window 都是
            //    'currentIndex: window.currentIndex' 单向 Qt Binding,直接赋值会永久打破.
            //    打破后, 后续 currentIndex(window) 变化无法同步到 stack,
            //    症状: 点底部页面后再点顶部, 导航栏跟过去但内容区还卡在底部页.
            //    现在只改 source (window.currentIndex), stack 自动跟随.
            //
            // ⚠️ 双动画 bug 修复: currentIndex = pageIndex 会触发
            //    NavigationPanelCore.onCurrentIndexChanged → _updateIndicatorWithAnimation,
            //    而 pageIndex 是页面索引(可能 8),不是导航 item 索引,_getItemAt(8) 取错位置 →
            //    indicator 闪一下到错位置; 然后 updateIndicatorForBottomItem 才跑正确动画。
            //    用 _skipIndicatorAnimation 标志临时屏蔽这次 onCurrentIndexChanged 的动画路径,
            //    让 updateIndicatorForBottomItem 独占动画。Backward(从底部回顶部)走的是
            //    _onItemClicked → 顶部 itemClicked signal,跟这里无关,所以 backward 动画完整。
            navPanel._skipIndicatorAnimation = true
            currentIndex = pageIndex
            navPanel._skipIndicatorAnimation = false
            currentPageChanged(pageIndex)

            // Update indicator for bottom page item
            navPanel.updateIndicatorForBottomItem(item.key)
        }
        bottomItemClicked(index)
        return pageIndex
    }

    onMicaEnabledChanged: {
        if (_micaAvailable && MicaManager && _nativeHookReady) {
            MicaManager.setMicaEffect(window, micaEnabled, Enums.isDark)
        }
    }

    // 直接监听 ConfigManager 的 micaEnabledChanged signal,作为 binding 链路
    // 失效时的兜底 (例如外部代码 .connect() 而不通过 property binding 改值,
    // 或 QML binding 求值次序问题导致 onMicaEnabledChanged 没触发)。
    // 这里读 ConfigManager 当前值并 apply,确保 DWM 状态与配置一致。
    Connections {
        target: typeof ConfigManager !== "undefined" ? ConfigManager : null
        function onMicaEnabledChanged() {
            if (window._micaAvailable && MicaManager && window._nativeHookReady) {
                MicaManager.setMicaEffect(window, ConfigManager.micaEnabled, Enums.isDark)
            }
        }
    }
    
    Connections {
        target: ThemeManager
        enabled: window._micaActive
        function onThemeChanged() {
            if (window._micaActive && MicaManager) MicaManager.updateDarkMode(Enums.isDark)
        }
    }
    
    // Initialize Mica effect on startup 启动时初始化云母效果
    // 无论 micaEnabled 是 true 或 false 都 apply,确保从持久化的"关闭"状态
    // 启动时 DWM backdrop 被显式设为 NONE,避免某些 Win11 默认 backdrop 行为
    // 导致"持久化关闭后重启仍看到 Mica"。
    //
    // ⚠️ 关键时序: 必须等 WindowsCore 的 _dwmDelayTimer 跑完才能设 Mica。
    //    shadow.enableShadowForWindow / NativeWindow.attach 都会发 SWP_FRAMECHANGED,
    //    会重置 DWM 的 DWMWA_SYSTEMBACKDROP_TYPE 为 NONE。
    //    在它们之前调 setMicaEffect 表面上 S_OK,实际被 FRAMECHANGED 清空。
    //    等 WindowsCore 发 nativeHookReady 信号后再设,才稳定。
    Connections {
        target: window
        enabled: window._micaAvailable
        function onNativeHookReady() {
            window._nativeHookReady = true
            if (MicaManager) {
                MicaManager.setMicaEffect(window, window.micaEnabled, Enums.isDark)
            }
        }
    }
}
