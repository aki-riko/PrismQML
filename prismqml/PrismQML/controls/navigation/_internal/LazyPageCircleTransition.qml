// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import "../../.."
import "../../feedback/_internal" as FeedbackInternal

// LazyPageCircleTransition - Hybrid single-circle transition for lazy pages 懒加载页面混合单圆过渡
Item {
    id: transition

    // ==================== Readonly State 只读状态 ====================
    readonly property bool running: radiusTransition.running
    readonly property bool active:
        _capturePending || _overlayFrameStage > 0 || _dissolving
        || _usingPageLayer || _inWindowStartPending
        || _mainFramePending || radiusTransition.running
    readonly property bool collapsing: radiusTransition.collapsing
    readonly property bool collapsed: _collapsed
    readonly property real progress: radiusTransition.progress
    readonly property var _hostWindow: transition.Window.window
    readonly property bool _hasLoaderItem: _sourceItem
        && typeof _sourceItem.item !== "undefined" && _sourceItem.item
    readonly property Item _captureItem: _hasLoaderItem
        ? _sourceItem.item
        : _sourceItem

    // ==================== Public Props 公开属性 ====================
    property int revealDuration: Enums.lazyLoadingTransitionMetrics.revealDuration
    // Forwarded to the radius animation; see QMLPageCircleTransition.
    // 转发给半径动画; 见 QMLPageCircleTransition。
    property int revealEasing: Easing.OutQuint
    property bool revealTarget: false
    // Keep external reveal sources hidden after expansion so the next window can show through.
    // 外部窗口揭幕后保持源项隐藏, 让后方窗口直接透出。
    property bool keepSourceHiddenOnExpand: false

    // ==================== Internal Props 内部属性 ====================
    property Item _sourceItem: null
    property bool _savedVisible: false
    property bool _collapsed: false
    property bool _capturePending: false
    property bool _captureCollapsing: false
    property int _overlayFrameStage: 0
    property bool _dissolving: false
    property bool _usingPageLayer: false
    property bool _inWindowStartPending: false
    property bool _mainFramePending: false
    property int _captureGeneration: 0
    property real _sourceStartX: 0
    property real _sourceStartY: 0
    property var _grabResult: null
    property string _lastFallbackReason: ""
    property bool _savedLayerEnabled: false
    property var _savedLayerEffect: null
    property bool _savedLayerSmooth: false

    // ==================== Signals 信号 ====================
    signal collapseStarted()
    signal expandStarted()
    signal collapseFinished()
    signal expandFinished()

    // ==================== Public Methods 公开方法 ====================
    function collapse(sourceItem) {
        return transition._beginTransition(sourceItem, true)
    }

    function expand(sourceItem) {
        return transition._beginTransition(sourceItem, false)
    }

    function stop() {
        transition._captureGeneration += 1
        transition._capturePending = false
        transition._overlayFrameStage = 0
        transition._dissolving = false
        transition._inWindowStartPending = false
        transition._mainFramePending = false
        // Child ids may already be null when Component.onDestruction invokes stop().
        // Component.onDestruction 调用 stop() 时，子对象 id 可能已经为空。
        if (captureTimeout) captureTimeout.stop()
        if (mainFrameFallback) mainFrameFallback.stop()
        if (radiusTransition) radiusTransition.stop()
        if (overlayWindow) overlayWindow.visible = false
        transition._restorePageLayer()
        transition._detach(true)
        if (frozenFrame) transition._releaseSnapshot()
        else transition._grabResult = null
        transition._collapsed = false
    }

    // ==================== Internal Methods 内部方法 ====================
    function _attach(sourceItem) {
        if (!sourceItem) return false

        transition._sourceItem = sourceItem
        transition._savedVisible = sourceItem.visible
        transition._sourceStartX = sourceItem.x
        transition._sourceStartY = sourceItem.y
        return true
    }

    function _beginTransition(sourceItem, collapsing) {
        transition.stop()
        transition._lastFallbackReason = ""
        if (!transition._attach(sourceItem) || !transition._captureItem) {
            transition._completeWithoutAnimation(collapsing, "source item unavailable")
            return false
        }

        transition._captureCollapsing = collapsing
        transition._collapsed = false
        if (transition._hostWindow) {
            return transition._beginPageLayerTransition(collapsing)
        }
        // Keep the complete page container renderable while grabToImage is pending;
        // the first overlay frame hides it before the radius animation starts.
        // 抓图等待期间保持完整页面容器可渲染；覆盖窗首帧上屏后才隐藏真实页。
        transition._sourceItem.visible = true
        return transition._beginSnapshotCapture(collapsing)
    }

    function _beginPageLayerTransition(collapsing) {
        var sourceItem = transition._sourceItem
        if (!sourceItem || !sourceItem.layer) {
            transition._completeWithoutAnimation(
                collapsing, "page layer unavailable", true)
            return false
        }

        transition._savedLayerEnabled = sourceItem.layer.enabled
        transition._savedLayerEffect = sourceItem.layer.effect
        transition._savedLayerSmooth = sourceItem.layer.smooth
        sourceItem.visible = true
        sourceItem.layer.smooth = true
        sourceItem.layer.effect = pageLayerEffect
        sourceItem.layer.enabled = true
        transition._usingPageLayer = true
        transition._inWindowStartPending = true
        transition._dissolving = true
        radiusTransition.prepare(collapsing)
        transition._hostWindow.requestUpdate()
        return true
    }

    function _beginSnapshotCapture(collapsing) {
        transition._captureGeneration += 1
        transition._capturePending = true
        transition._syncOverlayGeometry()
        frozenFrame.source = ""
        var generation = transition._captureGeneration
        return transition._captureWithItem(generation, collapsing)
    }

    function _captureWithItem(generation, collapsing) {
        var accepted = transition._captureItem.grabToImage(function(result) {
            if (!transition._capturePending ||
                    generation !== transition._captureGeneration) return
            transition._grabResult = result
            frozenFrame.source = result.url
            transition._showOverlayWhenReady()
        })
        if (!accepted) {
            transition._completeWithoutAnimation(collapsing, "grab request rejected")
            return false
        }
        captureTimeout.restart()
        return true
    }

    function _syncOverlayGeometry() {
        var captureItem = transition._captureItem
        if (!captureItem) return

        var globalPosition = captureItem.mapToGlobal(0, 0)
        overlayWindow.x = Math.round(globalPosition.x)
        overlayWindow.y = Math.round(globalPosition.y)
        overlayWindow.width = Math.max(1, Math.round(captureItem.width))
        overlayWindow.height = Math.max(1, Math.round(captureItem.height))
    }

    function _showOverlayWhenReady() {
        if (!transition._capturePending || frozenFrame.status !== Image.Ready) return

        captureTimeout.stop()
        transition._capturePending = false
        radiusTransition.prepare(transition._captureCollapsing)
        // Collapse first presents an identical full-page snapshot. Expansion must
        // present the radius-zero mask on its very first frame to avoid a full-page flash.
        // 收紧先呈现与旧页一致的整页快照；展开首帧必须直接是半径零，避免目标页整屏闪现。
        transition._dissolving = !transition._captureCollapsing
        transition._overlayFrameStage = transition._captureCollapsing ? 1 : 2
        frozenFrame.visible = true
        frozenFrame.opacity = Enums.opacityLevel.visible
        overlayWindow.visible = true
        overlayWindow.requestUpdate()
    }

    function _handleOverlayFrameSwapped() {
        if (transition._overlayFrameStage === 1) {
            // The full old-page snapshot is now on screen. Prepare the identical
            // radius-one mask and wait for one more swap before hiding the real page.
            // 旧页整帧已上屏；再等待半径一遮罩上屏后才隐藏真实旧页。
            transition._dissolving = true
            transition._overlayFrameStage = 2
            overlayWindow.requestUpdate()
            return
        }

        if (transition._overlayFrameStage === 2) {
            transition._overlayFrameStage = 0
            if (transition._sourceItem) transition._sourceItem.visible = false
            if (transition._captureCollapsing) transition.collapseStarted()
            else transition.expandStarted()
            radiusTransition.startPrepared()
            return
        }

    }

    function _completeWithoutAnimation(collapsing, reason, expectedFallback) {
        if (expectedFallback) console.warn("LazyPageCircleTransition: " + reason)
        else console.error("LazyPageCircleTransition: " + reason)
        transition._lastFallbackReason = reason
        transition._capturePending = false
        transition._overlayFrameStage = 0
        transition._dissolving = false
        transition._inWindowStartPending = false
        transition._mainFramePending = false
        captureTimeout.stop()
        overlayWindow.visible = false
        var sourceItem = transition._sourceItem
        if (sourceItem) sourceItem.visible = !collapsing
        transition._restorePageLayer()
        transition._detach(false)
        transition._releaseSnapshot()
        transition._collapsed = collapsing
        if (collapsing) {
            transition.collapseStarted()
            transition.collapseFinished()
        } else {
            transition.expandStarted()
            transition.expandFinished()
        }
    }

    function _releaseSnapshot() {
        frozenFrame.visible = false
        frozenFrame.source = ""
        transition._grabResult = null
    }

    function _restorePageLayer() {
        var sourceItem = transition._sourceItem
        if (!sourceItem || !transition._usingPageLayer) return

        sourceItem.layer.effect = transition._savedLayerEffect
        sourceItem.layer.smooth = transition._savedLayerSmooth
        sourceItem.layer.enabled = transition._savedLayerEnabled
        transition._usingPageLayer = false
        transition._inWindowStartPending = false
    }

    function _detach(restoreVisibility) {
        var sourceItem = transition._sourceItem
        if (!sourceItem) return

        if (restoreVisibility) sourceItem.visible = transition._savedVisible
        transition._sourceItem = null
    }

    function _handleRadiusFinished() {
        if (!transition._dissolving) return
        if (radiusTransition.collapsing) {
            transition._finalizeCollapse()
            return
        }

        // Keep the final full-page snapshot above the real target until the target
        // window has rendered and swapped one frame of its own.
        // 最终整页快照继续覆盖真实目标页，直到目标窗口完成一次实际渲染换帧。
        var sourceItem = transition._sourceItem
        if (sourceItem && !transition.keepSourceHiddenOnExpand)
            sourceItem.visible = true
        if (!transition._hostWindow) {
            transition._finalizeExpansion()
            return
        }
        transition._mainFramePending = true
        mainFrameFallback.restart()
        transition._hostWindow.requestUpdate()
    }

    function _finalizeCollapse() {
        var sourceItem = transition._sourceItem
        transition._dissolving = false
        if (sourceItem) sourceItem.visible = false
        transition._restorePageLayer()
        overlayWindow.visible = false
        transition._detach(false)
        transition._releaseSnapshot()
        transition._collapsed = true
        transition.collapseFinished()
    }

    function _finalizeExpansion() {
        mainFrameFallback.stop()
        var sourceItem = transition._sourceItem
        transition._mainFramePending = false
        transition._dissolving = false
        if (sourceItem)
            sourceItem.visible = transition.keepSourceHiddenOnExpand ? false : true
        transition._restorePageLayer()
        overlayWindow.visible = false
        transition._detach(false)
        transition._releaseSnapshot()
        transition._collapsed = false
        transition.expandFinished()
    }

    function _handleSourceWindowFrameSwapped() {
        if (transition._inWindowStartPending) {
            transition._inWindowStartPending = false
            if (transition._captureCollapsing) transition.collapseStarted()
            else transition.expandStarted()
            radiusTransition.startPrepared()
            return
        }
        if (!transition._mainFramePending) return
        transition._finalizeExpansion()
    }

    visible: false
    Component.onDestruction: transition.stop()

    FeedbackInternal.QMLPageCircleTransition {
        id: radiusTransition

        objectName: "qmlPageCircleTransition"
        revealDuration: transition.revealDuration
        revealEasing: transition.revealEasing
        onFinished: transition._handleRadiusFinished()
    }

    Timer {
        id: captureTimeout

        interval: Enums.duration.normal
        onTriggered: {
            if (!transition._capturePending) return
            transition._completeWithoutAnimation(
                transition._captureCollapsing, "snapshot capture timed out", true)
        }
    }

    Timer {
        id: mainFrameFallback

        interval: Enums.duration.ultraFast
        repeat: false
        onTriggered: {
            if (transition._mainFramePending) transition._finalizeExpansion()
        }
    }

    Component {
        id: pageLayerEffect

        FeedbackInternal.QMLPageCircleFrame {
            progress: radiusTransition.progress
            revealTarget: transition.revealTarget
        }
    }

    Connections {
        target: transition._hostWindow

        function onFrameSwapped() { transition._handleSourceWindowFrameSwapped() }
    }

    Window {
        id: overlayWindow

        objectName: "lazyPageCircleOverlayWindow"
        visible: false
        opacity: Enums.opacityLevel.visible
        color: Enums.transparent
        flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoFluentShadowWindowHint
        transientParent: null

        onFrameSwapped: transition._handleOverlayFrameSwapped()

        FeedbackInternal.QMLPageCircleFrame {
            id: circleFrame

            objectName: "lazyPageCircleFrame"
            width: parent.width
            height: parent.height
            x: transition._sourceItem
                ? transition._sourceItem.x - transition._sourceStartX : 0
            y: transition._sourceItem
                ? transition._sourceItem.y - transition._sourceStartY : 0
            opacity: transition._sourceItem
                ? transition._sourceItem.opacity : Enums.opacityLevel.visible
            scale: transition._sourceItem
                ? transition._sourceItem.scale : Enums.opacityLevel.visible
            transformOrigin: transition._sourceItem
                ? transition._sourceItem.transformOrigin : Item.Center
            source: frozenFrame
            progress: radiusTransition.progress
            revealTarget: transition.revealTarget
            visible: transition._dissolving
            z: Enums.zIndex.popup
        }

        Image {
            id: frozenFrame

            objectName: "lazyPageFrozenFrame"
            x: transition._dissolving ? (parent.width - width) / 2 : 0
            y: transition._dissolving ? (parent.height - height) / 2 : 0
            width: transition._dissolving ? Enums.border.thin : parent.width
            height: transition._dissolving ? Enums.border.thin : parent.height
            source: ""
            fillMode: Image.Stretch
            cache: false
            asynchronous: false
            smooth: true
            transformOrigin: Item.Center
            onStatusChanged: {
                if (status === Image.Ready) {
                    transition._showOverlayWhenReady()
                } else if (status === Image.Error && transition._capturePending) {
                    transition._completeWithoutAnimation(
                        transition._captureCollapsing, "snapshot image load failed")
                }
            }
        }

    }
}
