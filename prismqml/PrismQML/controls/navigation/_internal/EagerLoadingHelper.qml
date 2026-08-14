// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// EagerLoadingHelper - Staged runtime eager page activation 运行时 eager 页面分片激活
Item {
    id: helper

    // ==================== Required Props 必需属性 ====================
    required property var loaders
    required property int count
    required property bool lazyLoading
    required property bool sourceMode

    // ==================== Internal Props 内部属性 ====================
    property bool ready: true
    property bool activationActive: false
    property int cursor: -1
    property int requestedIndex: -1

    // ==================== Internal Methods 内部方法 ====================
    function start() {
        if (!sourceMode || count <= 1) {
            cancel()
            return
        }
        ready = false
        activationActive = false
        cursor = -1
        requestedIndex = -1
        activationTimer.start()
    }

    function cancel() {
        activationTimer.stop()
        ready = true
        activationActive = false
        cursor = -1
        requestedIndex = -1
    }

    function request(index) {
        if (sourceMode && !lazyLoading && index >= 0 && index < count) {
            requestedIndex = index
        }
    }

    function isPageLoaded(index) {
        if (!sourceMode || lazyLoading || ready) return true
        return loaders[index] && loaders[index].status === Loader.Ready
    }

    function _allPagesLoaded() {
        for (var i = 0; i < count; i++) {
            if (!loaders[i] || loaders[i].status !== Loader.Ready) return false
        }
        return true
    }

    // ==================== Content 内容 ====================
    Timer {
        id: activationTimer

        interval: Enums.duration.tick
        repeat: true
        onTriggered: {
            if (helper.lazyLoading || helper.ready) {
                stop()
                return
            }
            if (helper.cursor < helper.count - 1) {
                helper.activationActive = true
                helper.cursor += 1
                return
            }
            if (!helper._allPagesLoaded()) return
            helper.activationActive = false
            helper.ready = true
            helper.requestedIndex = -1
            stop()
        }
    }
}
