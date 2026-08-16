// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedLazyHelperLoader - Lazy helper Loader for StackedWidget
// StackedLazyHelperLoader - StackedWidget 的懒加载辅助器 Loader
Loader {
    id: lazyHelperLoader

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Size 尺寸 ====================
    anchors.fill: parent
    active: false
    asynchronous: host._asynchronousPageLoaderEnabled

    // ==================== Signals 信号 ====================
    onActiveChanged: host._traceLazyStage(
        "stacked.helper_loader.active_changed", host.currentIndex,
        "", lazyHelperLoader)
    onStatusChanged: host._traceLazyStage(
        "stacked.helper_loader.status_changed", host.currentIndex,
        "", lazyHelperLoader)
    onLoaded: {
        host._traceLazyStage(
            "stacked.helper_loader.loaded.begin", host.currentIndex,
            "", lazyHelperLoader)
        host._configureLazyHelper(item)
        host.profileTime("lazyHelper loaded")
        host._flushPendingLazySwitch()
        host._traceLazyStage(
            "stacked.helper_loader.loaded.done", host.currentIndex,
            "", lazyHelperLoader)
    }
}
