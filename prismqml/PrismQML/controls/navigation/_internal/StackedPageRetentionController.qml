// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick

// StackedPageRetentionController - Opt-in source page residency 页面驻留控制
Item {
    id: controller

    // ==================== Required Props 必需属性 ====================
    required property Item host

    function loaderActive(index, loader) {
        if (!host.lazyLoading || host.pageRetentionRadius < 0) {
            return index === host._displayIndex || Boolean(loader._loadOnce)
        }
        if (host._retentionTransitionActive && index === host.previousIndex) return true
        if (host.dynamicStack && host._dynamicDepth >= 0 &&
                index >= host._dynamicDepth &&
                index < host._dynamicDepth + Math.max(0, host.dynamicStackRetainDepth)) {
            return true
        }
        var radius = Math.max(0, host.pageRetentionRadius)
        return Math.abs(index - host.currentIndex) <= radius ||
                Math.abs(index - host._displayIndex) <= radius
    }

    visible: false
}
