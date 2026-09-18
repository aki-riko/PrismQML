// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedDynamicController - Dynamic source-page stack orchestration 动态源页面栈编排
Item {
    id: controller

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Internal Methods 内部方法 ====================
    // Retained (cached) popped levels. 0 means "destroy on pop" as before.
    // 保留（缓存）的已弹出层数。0 表示沿用旧的「弹出即销毁」。
    function _retainLevels() {
        return host.dynamicStack && host.dynamicStackRetainDepth > 0
                ? host.dynamicStackRetainDepth : 0
    }

    // ==================== Public Methods 公开方法 ====================
    function push(source, properties) {
        if (!host.dynamicStack || !host._useSourceMode || !source) return -1

        var logicalDepth = host._dynamicDepth >= 0 ? host._dynamicDepth : host.count
        var nextProperties = properties && typeof properties === "object"
                ? properties : ({})
        var cachedSource = _retainLevels() > 0 && logicalDepth < host._safePageSources.length
                ? host._safePageSources[logicalDepth] : undefined

        // Cache hit: this level still holds a live page for the same URL. Keep the
        // existing sources so the Loader (and its item) survives, and only refresh
        // the properties. StackedSourcePages then updates the live item in place.
        // 命中缓存：该层仍持有同一 URL 的存活页面。保留原 pageSources 让 Loader
        // 与页面实例继续存活，只更新属性；StackedSourcePages 会就地写回页面。
        if (cachedSource !== undefined && cachedSource !== null
                && String(cachedSource) === String(source)) {
            var reusedProperties = host._safePageProperties.slice()
            while (reusedProperties.length < logicalDepth) reusedProperties.push({})
            reusedProperties[logicalDepth] = nextProperties
            host.pageProperties = reusedProperties
            host._dynamicDepth = logicalDepth + 1
            host.currentIndex = host._dynamicDepth - 1
            return host.currentIndex
        }

        var sources = host._safePageSources.slice(0, logicalDepth)
        var props = host._safePageProperties.slice(0, logicalDepth)
        sources.push(source)
        props.push(nextProperties)
        host.pageProperties = props
        host.pageSources = sources
        host._dynamicDepth = sources.length
        host.currentIndex = host._dynamicDepth - 1
        return host.currentIndex
    }

    function pop() {
        if (!host.dynamicStack || host._dynamicDepth <= 1) return false
        var targetDepth = host._dynamicDepth - 1
        host._pendingTrimDepth = targetDepth
        host.currentIndex = targetDepth - 1
        return true
    }

    function popTo(targetDepth) {
        if (!host.dynamicStack || host._dynamicDepth <= 1) return false
        var normalizedDepth = Math.max(1, Math.min(Number(targetDepth), host._dynamicDepth))
        if (normalizedDepth >= host._dynamicDepth) return false
        host._pendingTrimDepth = normalizedDepth
        host.currentIndex = normalizedDepth - 1
        return true
    }

    function trimPendingPages() {
        if (host._pendingTrimDepth < 0) return
        var targetDepth = host._pendingTrimDepth
        host._pendingTrimDepth = -1
        // Keep up to `dynamicStackRetainDepth` popped levels alive so returning to
        // the same URL reuses the live page. With retainDepth 0 this is exactly the
        // historical truncation to the logical depth.
        // 按 dynamicStackRetainDepth 保留已弹出层，使再次进入同一 URL 时复用存活页面。
        // retainDepth 为 0 时与旧的「截断到逻辑深度」完全一致。
        var keepDepth = targetDepth + _retainLevels()
        if (host._safePageSources.length > keepDepth) {
            host.pageProperties = host._safePageProperties.slice(0, keepDepth)
            host.pageSources = host._safePageSources.slice(0, keepDepth)
        }
        host._dynamicDepth = targetDepth
    }

    visible: false
}
