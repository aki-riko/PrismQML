// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// StackedSourcePages - Source-backed page container for StackedWidget
// StackedSourcePages - StackedWidget 的 pageSources 页面容器
Item {
    id: sourceContainer

    // ==================== Required Props 必需属性 ====================
    required property Item host
    required property var eagerHelper

    // ==================== Size 尺寸 ====================
    visible: host._useSourceMode

    // ==================== Content 内容 ====================
    Repeater {
        id: sourceRepeater

        model: sourceContainer.host._useSourceMode
               ? sourceContainer.host._safePageSources.length : 0

        Loader {
            id: sourceLoader

            property bool _loadOnce: false
            property int pageIndex: index

            width: sourceContainer.width
            height: sourceContainer.height
            // Latch loading with _loadOnce instead of active to avoid self-reference.
            // 使用独立 _loadOnce 锁存加载状态，避免 active 自引用导致全量加载。
            onActiveChanged: {
                if (active) _loadOnce = true
                sourceContainer.host._traceLazyStage(
                    "stacked.source_loader.active_changed", index, "", sourceLoader)
            }
            onStatusChanged: sourceContainer.host._traceLazyStage(
                "stacked.source_loader.status_changed", index, "", sourceLoader)
            source: sourceContainer.host.lazyLoading
                    ? (index === sourceContainer.host._displayIndex || _loadOnce
                       ? (sourceContainer.host._safePageSources[index] || "") : "")
                    : (sourceContainer.host._safePageSources[index] || "")
            active: sourceContainer.host.lazyLoading
                    ? (index === sourceContainer.host._displayIndex || _loadOnce)
                    : (index === sourceContainer.host._displayIndex ||
                       sourceContainer.eagerHelper.ready ||
                       (sourceContainer.eagerHelper.activationActive &&
                        index <= sourceContainer.eagerHelper.cursor) ||
                       index === sourceContainer.eagerHelper.requestedIndex)
            visible: index === sourceContainer.host._displayIndex
            opacity: index === sourceContainer.host._displayIndex ? 1 : 0
            scale: 1
            transformOrigin: Item.Center
            asynchronous: sourceContainer.host.lazyLoading &&
                          sourceContainer.host._asynchronousPageLoaderEnabled

            Component.onCompleted: {
                var loaders = sourceContainer.host._loaders.slice()
                loaders[index] = sourceLoader
                sourceContainer.host._loaders = loaders
                sourceContainer.host.profileTime("sourceLoader registered index=" + index)
            }
            Component.onDestruction: {
                if (!sourceContainer.host || sourceContainer.host._destroying) return
                var loaders = sourceContainer.host._loaders.slice()
                var registeredIndex = pageIndex
                if (registeredIndex >= 0 && loaders[registeredIndex] === sourceLoader) {
                    loaders[registeredIndex] = null
                    while (loaders.length > 0 && !loaders[loaders.length - 1]) loaders.pop()
                    sourceContainer.host._loaders = loaders
                }
            }

            // Latch after actual load completion; this also covers the initial page.
            // 在实际加载完成后锁存，也覆盖启动时 active 未发生变化的首页。
            onLoaded: {
                sourceContainer.host._traceLazyStage(
                    "stacked.source_loader.loaded.begin", index, "", sourceLoader)
                _loadOnce = true
                sourceContainer.host.pageLoaded(index)
                sourceContainer.host.profileTime("sourceLoader onLoaded index=" + index)
                sourceContainer.host._traceLazyStage(
                    "stacked.source_loader.loaded.done", index, "", sourceLoader)
            }
        }
    }
}
