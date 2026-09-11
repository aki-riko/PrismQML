// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedPageApi - Public page lookup and navigation helpers 页面查询与导航助手
Item {
    id: api

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Public Methods 公开方法 ====================
    function setCurrentWidget(widget) {
        for (var i = 0; i < host.count; i++) {
            if (api.widget(i) === widget) {
                host.setCurrentIndex(i)
                return true
            }
        }
        return false
    }

    function widget(index) {
        if (index < 0 || index >= host.count) return null
        if (host._useSourceMode) return host._loaders[index] || null
        return host.containerItem.children[index]
    }

    function next() {
        if (host.currentIndex < host.count - 1) {
            host.setCurrentIndex(host.currentIndex + 1)
            return true
        }
        return false
    }

    function previous() {
        if (host.currentIndex > 0) {
            host.setCurrentIndex(host.currentIndex - 1)
            return true
        }
        return false
    }

    function indexOf(item) {
        if (host._useSourceMode) {
            for (var i = 0; i < host._loaders.length; i++) {
                if (host._loaders[i] && host._loaders[i].item === item) return i
            }
        } else {
            for (var j = 0; j < host.containerItem.children.length; j++) {
                if (host.containerItem.children[j] === item) return j
            }
        }
        return -1
    }

    function itemAt(index) {
        return api.widget(index)
    }

    visible: false
}
