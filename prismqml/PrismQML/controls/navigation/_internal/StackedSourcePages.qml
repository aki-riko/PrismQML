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

    // Keep dynamic-stack delegates stable when a new URL is appended. A numeric
    // Repeater model may rebuild all delegates on pageSources replacement,
    // which reloads the currently visible page and exposes a blank frame.
    // 动态栈追加 URL 时保持委托稳定。数值 Repeater 模型在替换 pageSources 后
    // 可能重建全部委托，导致当前页重载并暴露空白帧。
    function _syncPageModel() {
        var sources = sourceContainer.host._safePageSources
        while (sourceModel.count > sources.length) {
            sourceModel.remove(sourceModel.count - 1)
        }
        for (var index = 0; index < sources.length; index++) {
            var source = sources[index] || ""
            if (index >= sourceModel.count) {
                sourceModel.append({"sourceValue": source})
            } else if (String(sourceModel.get(index).sourceValue)
                       !== String(source)) {
                sourceModel.setProperty(index, "sourceValue", source)
            }
        }
        if (sourceContainer.host._loaders.length > sources.length) {
            sourceContainer.host._loaders = sourceContainer.host._loaders.slice(
                0, sources.length)
        }
    }

    // ==================== Content 内容 ====================
    ListModel {
        id: sourceModel
    }

    Repeater {
        id: sourceRepeater

        model: sourceModel

        Loader {
            id: sourceLoader

            property bool _loadOnce: false
            property int pageIndex: index
            property string _loadedSourceText: ""

            function _syncSource() {
                var modelEntry = index >= 0 && index < sourceModel.count
                        ? sourceModel.get(index) : null
                var nextSource = modelEntry ? modelEntry.sourceValue : ""
                var nextProperties = sourceContainer.host._pagePropertiesFor(index)
                if (!nextSource) {
                    sourceLoader.source = ""
                    sourceLoader._loadedSourceText = ""
                    return
                }
                var nextSourceText = nextSource && nextSource.toString
                        ? nextSource.toString() : String(nextSource)
                if (sourceLoader.item && sourceLoader._loadedSourceText === nextSourceText) {
                    var keys = Object.keys(nextProperties)
                    for (var i = 0; i < keys.length; i++) {
                        var key = keys[i]
                        if (key in sourceLoader.item) sourceLoader.item[key] = nextProperties[key]
                    }
                    return
                }
                if (sourceLoader.source.toString() !== nextSourceText) {
                    sourceLoader._loadedSourceText = nextSourceText
                    sourceLoader.setSource(nextSource, nextProperties)
                    return
                }
                if (sourceLoader.item) {
                    var keys = Object.keys(nextProperties)
                    for (var i = 0; i < keys.length; i++) {
                        var key = keys[i]
                        if (key in sourceLoader.item) sourceLoader.item[key] = nextProperties[key]
                    }
                }
            }

            width: sourceContainer.width
            height: sourceContainer.height
            // Latch loading with _loadOnce instead of active to avoid self-reference.
            // 使用独立 _loadOnce 锁存加载状态，避免 active 自引用导致全量加载。
            onActiveChanged: {
                if (active) {
                    _loadOnce = true
                    sourceLoader._syncSource()
                }
                sourceContainer.host._traceLazyStage(
                    "stacked.source_loader.active_changed", index, "", sourceLoader)
            }
            onStatusChanged: sourceContainer.host._traceLazyStage(
                "stacked.source_loader.status_changed", index, "", sourceLoader)
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
            // Use sliced incubation for eager pages too when the runtime marks
            // the Qt build safe. Eager mode still activates every page, but
            // creation is spread across GUI frames instead of one blocking
            // synchronous burst. Unsafe Qt builds retain the synchronous
            // fallback selected by the shared incubation policy.
            // 运行时判定 Qt 构建安全时，eager 页面也使用分片孵化。eager 模式仍会激活
            // 全部页面，但创建过程分摊到多个 GUI 帧，不再形成一次同步长阻塞；不安全
            // 的 Qt 构建继续沿用共享孵化策略选出的同步回退。
            asynchronous: sourceContainer.host._asynchronousPageLoaderEnabled

            Component.onCompleted: {
                var loaders = sourceContainer.host._loaders.slice()
                loaders[index] = sourceLoader
                sourceContainer.host._loaders = loaders
                sourceContainer.host.profileTime("sourceLoader registered index=" + index)
                if (sourceLoader.active) sourceLoader._syncSource()
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
                sourceLoader._loadedSourceText = sourceLoader.source.toString()
                sourceContainer.host.pageLoaded(index)
                sourceContainer.host.profileTime("sourceLoader onLoaded index=" + index)
                sourceContainer.host._traceLazyStage(
                    "stacked.source_loader.loaded.done", index, "", sourceLoader)
            }

            Connections {
                function onPageSourcesChanged() { sourceLoader._syncSource() }
                function onPagePropertiesChanged() { sourceLoader._syncSource() }

                target: sourceContainer.host
            }
        }
    }

    Connections {
        function onPageSourcesChanged() { sourceContainer._syncPageModel() }

        target: sourceContainer.host
    }

    Component.onCompleted: sourceContainer._syncPageModel()
}
