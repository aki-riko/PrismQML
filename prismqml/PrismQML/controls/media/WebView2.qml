// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal" as MediaInternal

// WebView2 - Embedded browser surface 内嵌浏览器
// Fluent parity for WebView2 on top of QtWebEngine. The engine is incubated on
// demand and the control degrades to a readable fallback when QtWebEngine is
// missing, instead of crashing during import.
// 基于 QtWebEngine 的 Fluent WebView2 对齐：引擎按需孵化；QtWebEngine 缺失时
// 优雅降级为可读回退界面，而不是在导入期崩溃。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property url surfaceUrl: Qt.resolvedUrl("_internal/WebEngineSurface.qml")   // Injected surface component 注入的表面组件
    property url url: ""                        // Injected page address 调用方注入的页面地址
    property real zoomFactor: Enums.media.webview_default_zoom
    property bool autoActivate: false           // Activate during construction 构造期是否激活
    property bool schedulerActive: true         // Runtime activation gate 运行时激活门控
    property string unavailableMessage: ""      // Localized fallback text 本地化回退文案

    // ==================== Readonly State 只读状态 ====================
    readonly property bool active: surfaceLoader.status !== Loader.Null
    readonly property bool loading: surfaceLoader.status === Loader.Loading
    readonly property bool surfaceCreated: surfaceLoader.item !== null
    readonly property bool available: _availability === Enums.media.availability_available
    readonly property bool degraded: _availability === Enums.media.availability_unavailable
    readonly property int availabilityState: _availability
    readonly property string errorString: _errorString
    readonly property bool pageLoading: _pageLoading
    readonly property int loadProgress: _loadProgress
    readonly property string title: _title
    readonly property url currentUrl: _currentUrl
    readonly property bool canGoBack: _canGoBack
    readonly property bool canGoForward: _canGoForward

    // ==================== Internal Props 内部属性 ====================
    property int _availability: Enums.media.availability_unknown
    property string _errorString: ""
    property bool _pageLoading: false
    property int _loadProgress: 0
    property string _title: ""
    property url _currentUrl: ""
    property bool _canGoBack: false
    property bool _canGoForward: false
    property var _probeComponent: null
    property string _pendingHtml: ""
    property url _pendingHtmlBaseUrl: ""
    property bool _hasPendingHtml: false
    property bool _activationRequested: false

    // ==================== Signals 信号 ====================
    signal activated()
    signal availabilityFailed(string message)
    signal pageLoadStarted()
    signal pageLoadFinished(bool succeeded)
    signal navigationStateChanged()

    // ==================== Public Methods 公开方法 ====================
    // Incubate the browser surface 孵化浏览器表面
    function activate() {
        _activationRequested = true
        if (!schedulerActive) return false
        if (surfaceLoader.status !== Loader.Null) {
            return available
        }
        surfaceLoader.asynchronous = true
        surfaceLoader.setSource(surfaceUrl, { "host": control })
        return true
    }

    // Compile the surface without creating it 只编译表面而不创建实例
    // Returns true once the surface is known to be loadable; module resolution may
    // still be in flight, in which case the public availability state settles later.
    // 表面可加载时返回 true；模块解析可能仍在进行，此时公开可用性状态稍后落定。
    function probeAvailability() {
        if (_probeComponent === null) {
            _probeComponent = Qt.createComponent(surfaceUrl)
            _probeComponent.statusChanged.connect(control._applyProbeStatus)
        }
        return control._applyProbeStatus()
    }

    // Navigate to an address 导航到指定地址
    function load(address) {
        url = address
        activate()
    }

    // Replace the current address 替换当前地址
    function setUrl(address) {
        url = address
    }

    function reload() {
        if (surfaceLoader.item !== null) {
            surfaceLoader.item.requestReload()
        }
    }

    function stop() {
        if (surfaceLoader.item !== null) {
            surfaceLoader.item.requestStop()
        }
    }

    function goBack() {
        if (surfaceLoader.item !== null) {
            surfaceLoader.item.requestGoBack()
        }
    }

    function goForward() {
        if (surfaceLoader.item !== null) {
            surfaceLoader.item.requestGoForward()
        }
    }

    // Load inline markup 加载内联标记
    function loadHtml(html, baseUrl) {
        _pendingHtml = html
        _pendingHtmlBaseUrl = baseUrl === undefined ? "" : baseUrl
        _hasPendingHtml = true
        activate()
        if (surfaceLoader.item !== null) {
            surfaceLoader.item.requestLoadHtml(html, baseUrl)
            _hasPendingHtml = false
        }
    }

    // Run script inside the page 在页面内执行脚本
    function runJavaScript(script) {
        if (surfaceLoader.item !== null) {
            surfaceLoader.item.requestRunJavaScript(script)
        }
    }

    // ==================== Internal Methods 内部方法 ====================
    // Extract the incubation error text 提取孵化错误文本
    function _surfaceErrorText() {
        if (_probeComponent === null) {
            _probeComponent = Qt.createComponent(surfaceUrl)
            _probeComponent.statusChanged.connect(control._applyProbeStatus)
        }
        return _probeComponent.status === Component.Error
            ? _probeComponent.errorString()
            : "web surface component failed to load"
    }

    // Apply the probe result to the public availability state 把探测结果写入公开可用性状态
    function _applyProbeStatus() {
        if (_probeComponent === null) {
            return false
        }
        if (_probeComponent.status === Component.Error) {
            _availability = Enums.media.availability_unavailable
            _errorString = _probeComponent.errorString()
            return false
        }
        if (_probeComponent.status === Component.Ready) {
            _availability = Enums.media.availability_available
            _errorString = ""
            return true
        }
        return false
    }

    // Surface ready callback 表面就绪回调
    function _onSurfaceReady() {
        _availability = Enums.media.availability_available
        _errorString = ""
        if (_hasPendingHtml) {
            surfaceLoader.item.requestLoadHtml(_pendingHtml, _pendingHtmlBaseUrl)
            _hasPendingHtml = false
        }
        activated()
    }

    function _onLoadingChanged(started, succeeded) {
        _pageLoading = started
        if (started) {
            pageLoadStarted()
        } else {
            pageLoadFinished(succeeded)
        }
    }

    function _onLoadProgress(value) { _loadProgress = value }
    function _onTitle(value) { _title = value }
    function _onUrlChanged(value) { _currentUrl = value }

    function _onNavigationStateChanged(backAvailable, forwardAvailable) {
        _canGoBack = backAvailable
        _canGoForward = forwardAvailable
        navigationStateChanged()
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.media.media_default_width
    implicitHeight: Enums.media.media_default_height

    Component.onCompleted: {
        if (autoActivate) {
            activate()
        }
    }

    onSchedulerActiveChanged: {
        if (schedulerActive && _activationRequested &&
                surfaceLoader.status === Loader.Null) {
            activate()
        }
    }

    // ==================== Content 内容 ====================
    // Incubated browser surface 按需孵化的浏览器表面
    Loader {
        id: surfaceLoader
        anchors.fill: parent

        // Ready is reported here: an incubated surface runs its own
        // Component.onCompleted before the Loader exposes it to the host.
        // 就绪在这里上报：被孵化的表面自身的 Component.onCompleted 先于宿主可见。
        onLoaded: control._onSurfaceReady()

        onStatusChanged: {
            if (surfaceLoader.status === Loader.Error) {
                control._availability = Enums.media.availability_unavailable
                control._errorString = control._surfaceErrorText()
                control.availabilityFailed(control._errorString)
            }
        }
    }

    // Graceful fallback when QtWebEngine is unavailable QtWebEngine 不可用时的优雅回退
    Loader {
        id: unavailableLoader
        anchors.fill: parent
        active: control.degraded
        sourceComponent: MediaInternal.SurfaceUnavailable {
            host: control
        }
    }
}
