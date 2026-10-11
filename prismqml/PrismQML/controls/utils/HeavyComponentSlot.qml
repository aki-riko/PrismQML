// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick
import "../.."

// HeavyComponentSlot - Budgeted Loader wrapper for expensive QML content 重型 QML 内容预算 Loader
// The default is inert until scheduled is enabled, preserving ordinary Loader
// behavior for existing components.
// 默认未启用时不参与调度，保持现有组件的普通 Loader 行为。
Item {
    id: slot

    // ==================== Public Props 公开属性 ====================
    property Component sourceComponent: null
    property url source: ""
    property var initialProperties: ({})
    property bool scheduled: false
    property bool pageActive: true
    property bool inViewport: true
    // Optional viewport state object exposing an inViewport bool 可选视口状态对象，需暴露 inViewport 布尔属性
    property QtObject viewportState: null
    property bool preloadWhenOutOfViewport: false
    property bool keepAlive: true
    property bool incubate: true
    property int priority: HeavyComponentScheduler.priority_visible

    // ==================== Readonly State 只读状态 ====================
    readonly property var item: contentLoader.item
    readonly property int status: contentLoader.status
    readonly property bool loading: contentLoader.status === Loader.Loading
    readonly property bool loaded: contentLoader.status === Loader.Ready && item !== null
    // A bound viewport state takes precedence over the manual fallback.
    // 绑定视口状态优先于手动回退值。
    readonly property bool effectiveInViewport:
        viewportState === null ? inViewport : viewportState.inViewport
    readonly property bool workActive: enabled && pageActive && effectiveInViewport && loaded
    readonly property bool _runtimeIncubationEnabled:
        typeof PrismQmlAsynchronousPageLoaderEnabled === "undefined" ||
        PrismQmlAsynchronousPageLoaderEnabled

    // ==================== Internal Props 内部属性 ====================
    property bool _schedulerRequested: false
    property int _schedulerSequence: -1

    // ==================== Signals 信号 ====================
    signal loadedChangedExternally()
    signal loadFailed(string errorString)

    // ==================== Public Methods 公开方法 ====================
    function requestLoad() {
        _schedulerRequested = true
        HeavyComponentScheduler.requestActivation(slot)
    }

    function release() {
        _schedulerRequested = false
        HeavyComponentScheduler.cancelActivation(slot)
        if (!keepAlive) contentLoader.active = false
    }

    // ==================== Internal Methods 内部方法 ====================
    function _schedulerCanActivate() {
        return enabled && pageActive &&
                (effectiveInViewport || preloadWhenOutOfViewport)
    }

    function _schedulerNeedsActivation() {
        return !contentLoader.active &&
                (sourceComponent !== null || source.toString() !== "")
    }

    function _schedulerActivate() {
        if (!_schedulerNeedsActivation()) return false
        if (sourceComponent !== null) {
            contentLoader.sourceComponent = sourceComponent
        } else {
            contentLoader.setSource(source, initialProperties)
        }
        contentLoader.active = true
        return true
    }

    function _reloadAfterSourceChange() {
        if (!scheduled) return
        contentLoader.active = false
        requestLoad()
    }

    anchors.fill: parent

    onScheduledChanged: {
        if (scheduled) requestLoad()
        else release()
    }
    onPageActiveChanged: {
        if (!pageActive && !keepAlive) release()
        else if (scheduled && pageActive) requestLoad()
    }
    onEffectiveInViewportChanged: {
        if (!effectiveInViewport && !keepAlive) release()
        else if (scheduled && effectiveInViewport) requestLoad()
    }
    onEnabledChanged: {
        if (!enabled && !keepAlive) release()
        else if (scheduled && enabled) requestLoad()
    }
    onPreloadWhenOutOfViewportChanged: {
        if (scheduled && preloadWhenOutOfViewport) requestLoad()
    }
    onSourceChanged: _reloadAfterSourceChange()
    onSourceComponentChanged: _reloadAfterSourceChange()

    Component.onCompleted: {
        HeavyComponentScheduler.registerSlot(slot)
        if (scheduled) requestLoad()
    }
    Component.onDestruction: HeavyComponentScheduler.unregisterSlot(slot)

    // ==================== Content 内容 ====================
    Loader {
        id: contentLoader

        anchors.fill: parent
        active: false
        asynchronous: slot.incubate && slot._runtimeIncubationEnabled

        onLoaded: slot.loadedChangedExternally()
        onStatusChanged: {
            if (status === Loader.Error) slot.loadFailed(errorString())
        }
    }
}
