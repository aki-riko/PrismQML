// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedDiagnostics - Startup profiling and lazy-stage tracing 启动剖析与懒加载阶段追踪
// Owns the verbose diagnostic state and message formatting; StackedWidget keeps
// only thin delegators so its own size stays inside the modularization gate.
// 持有冗长诊断状态与消息拼装; StackedWidget 只保留薄委托, 使入口体积留在模块化门禁内。
Item {
    id: diagnostics

    // ==================== Required Props 必需属性 ====================
    required property Item host
    // Profiling baseline is injected so the reported total keeps measuring from
    // the host's own construction, not from this helper's creation.
    // 剖析基线由宿主注入, 保证总量仍从宿主构造时刻起算, 而非本助手的创建时刻。
    required property real profileStart

    // ==================== Internal Props 内部属性 ====================
    readonly property bool verboseActive: typeof PrismQmlStartupProfileVerbose !== "undefined" && PrismQmlStartupProfileVerbose
    property real profileLast: profileStart
    property int sequence: 0

    // ==================== Internal Methods 内部方法 ====================
    function profileTime(msg) {
        if (!verboseActive) return
        var now = Date.now()
        console.debug("[启动剖析] StackedWidget " + msg + ": +" +
                    Math.round(now - profileLast) + "ms / total " +
                    Math.round(now - profileStart) + "ms")
        profileLast = now
    }

    function loaderSnapshot(index, loaderOverride) {
        var loader = loaderOverride ||
                (index >= 0 && index < host._loaders.length ? host._loaders[index] : null)
        var targetSource = index >= 0 && index < host._safePageSources.length ?
                    String(host._safePageSources[index]) : ""
        var currentSource = host._displayIndex >= 0 && host._displayIndex < host._safePageSources.length ?
                    String(host._safePageSources[host._displayIndex]) : ""
        if (!loader) {
            return "loader=missing" +
                    " targetSource=\"" + targetSource + "\"" +
                    " currentSource=\"" + currentSource + "\""
        }
        var itemObjectName = loader.item && loader.item.objectName ?
                    loader.item.objectName : ""
        return "loader.active=" + loader.active +
                " loader.status=" + loader.status +
                " loader.item=" + (loader.item !== null) +
                " loader.source=\"" + String(loader.source) + "\"" +
                " loader.itemObjectName=\"" + itemObjectName + "\"" +
                " targetSource=\"" + targetSource + "\"" +
                " currentSource=\"" + currentSource + "\""
    }

    function traceLazyStage(stage, index, details, loaderOverride) {
        if (!verboseActive) return
        sequence += 1
        var detailText = details ? " " + details : ""
        console.debug("[懒加载诊断] StackedWidget #" + sequence +
                    " stage=" + stage +
                    " target=" + index +
                    " current=" + host.currentIndex +
                    " display=" + host._displayIndex +
                    " pending=" + host._pendingLazySwitchIndex + " " +
                    loaderSnapshot(index, loaderOverride) + detailText)
    }

    visible: false
}
