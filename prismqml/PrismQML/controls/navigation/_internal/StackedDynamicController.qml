// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedDynamicController - Dynamic source-page stack orchestration 动态源页面栈编排
Item {
    id: controller

    // ==================== Required Props 必需属性 ====================
    required property Item host

    visible: false

    // ==================== Public Methods 公开方法 ====================
    function push(source, properties) {
        if (!host.dynamicStack || !host._useSourceMode || !source) return -1

        var logicalDepth = host._dynamicDepth >= 0 ? host._dynamicDepth : host.count
        var sources = host._safePageSources.slice(0, logicalDepth)
        var props = host._safePageProperties.slice(0, logicalDepth)
        sources.push(source)
        props.push(properties && typeof properties === "object" ? properties : ({}))
        host.pageProperties = props
        host.pageSources = sources
        host._dynamicDepth = sources.length
        host.currentIndex = host._dynamicDepth - 1
        return host.currentIndex
    }

    function pop() {
        if (!host.dynamicStack || host._dynamicDepth <= 1) return false
        var targetDepth = host._dynamicDepth - 1
        host._dynamicDepth = targetDepth
        host._pendingTrimDepth = targetDepth
        host.currentIndex = targetDepth - 1
        if (host.currentIndex === host._displayIndex) trimPendingPages()
        return true
    }

    function popTo(targetDepth) {
        if (!host.dynamicStack || host._dynamicDepth <= 1) return false
        var normalizedDepth = Math.max(1, Math.min(Number(targetDepth), host._dynamicDepth))
        if (normalizedDepth >= host._dynamicDepth) return false
        host._dynamicDepth = normalizedDepth
        host._pendingTrimDepth = normalizedDepth
        host.currentIndex = normalizedDepth - 1
        if (host.currentIndex === host._displayIndex) trimPendingPages()
        return true
    }

    function trimPendingPages() {
        if (host._pendingTrimDepth < 0) return
        var targetDepth = host._pendingTrimDepth
        host._pendingTrimDepth = -1
        host.pageProperties = host._safePageProperties.slice(0, targetDepth)
        host.pageSources = host._safePageSources.slice(0, targetDepth)
        host._dynamicDepth = targetDepth
    }
}
