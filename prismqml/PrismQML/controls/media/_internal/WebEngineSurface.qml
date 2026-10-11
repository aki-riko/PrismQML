// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtWebEngine
import "../../.."

// WebEngineSurface - QtWebEngine browser surface QtWebEngine 浏览器表面
// Loaded lazily by WebView2 so the Chromium backend never starts during
// component construction. 由 WebView2 懒加载，避免构造期启动 Chromium 后端。
Item {
    id: surface

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Readonly State 只读状态 ====================
    readonly property var webView: engineView

    // ==================== Public Methods 公开方法 ====================
    function requestLoad(address) { engineView.url = address }
    function requestReload() { engineView.reload() }
    function requestStop() { engineView.stop() }
    function requestGoBack() { engineView.goBack() }
    function requestGoForward() { engineView.goForward() }
    function requestLoadHtml(html, baseUrl) { engineView.loadHtml(html, baseUrl) }
    function requestRunJavaScript(script) { engineView.runJavaScript(script) }

    // ==================== Size 尺寸 ====================
    anchors.fill: parent

    // ==================== Content 内容 ====================
    WebEngineView {
        id: engineView
        anchors.fill: parent
        url: surface.host.url
        zoomFactor: surface.host.zoomFactor
        backgroundColor: Enums.backgroundColor

        onLoadingChanged: function(loadRequest) {
            surface.host._onLoadingChanged(
                loadRequest.status === WebEngineView.LoadStartedStatus,
                loadRequest.status === WebEngineView.LoadSucceededStatus)
        }
        onLoadProgressChanged: surface.host._onLoadProgress(loadProgress)
        onTitleChanged: surface.host._onTitle(title)
        onUrlChanged: surface.host._onUrlChanged(url)
        onCanGoBackChanged: surface.host._onNavigationStateChanged(canGoBack, canGoForward)
        onCanGoForwardChanged: surface.host._onNavigationStateChanged(canGoBack, canGoForward)
    }
}
