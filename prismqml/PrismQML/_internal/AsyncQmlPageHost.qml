// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// AsyncQmlPageHost - Incubated page host without its own visual overlay 不包含自有视觉遮罩的分帧页面宿主
Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    property url pageSource: ""
    property var backend: null
    property bool loadRequested: false
    readonly property var contentItem: contentLoader.item
    property bool _targetReady: false
    property bool _pageLoadedReported: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool pageLoading: contentLoader.status === Loader.Loading
    readonly property bool pageReady: contentLoader.status === Loader.Ready && _targetReady

    // ==================== Signals 信号 ====================
    signal pageLoaded()
    signal pageLoadFailed(string source)

    // ==================== Internal Methods 内部方法 ====================
    function _startLoading() {
        if (!loadRequested || pageSource.toString() === "") return
        root._targetReady = false
        root._pageLoadedReported = false
        contentLoader.setSource(pageSource, {"backend": backend})
        contentLoader.active = true
    }

    function _readTargetReady() {
        if (!contentLoader.item) return false
        var declaredReady = contentLoader.item["prismqmlAsyncReady"]
        return declaredReady === undefined || declaredReady === true
    }

    function _syncTargetReady() {
        if (root._pageLoadedReported) return
        root._targetReady = root._readTargetReady()
        root._reportPageLoaded()
    }

    function _reportPageLoaded() {
        if (!root.pageReady || root._pageLoadedReported) return
        root._pageLoadedReported = true
        root.pageLoaded()
    }

    objectName: "prismAsyncQmlPageHost"
    visible: pageReady
    onLoadRequestedChanged: _startLoading()

    // ==================== Content 内容 ====================
    Loader {
        id: contentLoader

        anchors.fill: parent
        active: false
        asynchronous: true

        onLoaded: root._syncTargetReady()
        onStatusChanged: {
            if (status === Loader.Error) {
                root.pageLoadFailed(root.pageSource.toString())
            }
        }
    }

    Connections {
        function onPrismqmlAsyncReadyChanged() {
            root._syncTargetReady()
        }

        target: contentLoader.item
        ignoreUnknownSignals: true
    }
}
