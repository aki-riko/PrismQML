// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import "../../.."
import "../../feedback/_internal" as FeedbackInternal

// LazyPageCircleTransition - Native-overlay circle transition for lazy pages 懒加载页面原生覆盖窗圆形过渡
Item {
    id: transition

    // ==================== Readonly State 只读状态 ====================
    readonly property bool running: radiusTransition.running
    readonly property bool active:
        _capturePending || _overlayFramePending || _dissolving || radiusTransition.running
    readonly property bool collapsing: radiusTransition.collapsing
    readonly property bool collapsed: _collapsed
    readonly property real progress: radiusTransition.progress
    readonly property Item _captureItem: _sourceItem
        && typeof _sourceItem.item !== "undefined" && _sourceItem.item
        ? _sourceItem.item : _sourceItem

    // ==================== Internal Props 内部属性 ====================
    property Item _sourceItem: null
    property bool _savedVisible: false
    property bool _collapsed: false
    property bool _capturePending: false
    property bool _captureCollapsing: false
    property bool _overlayFramePending: false
    property bool _dissolving: false
    property int _captureGeneration: 0
    property real _sourceStartX: 0
    property real _sourceStartY: 0
    property var _grabResult: null

    // ==================== Signals 信号 ====================
    signal collapseFinished()
    signal expandFinished()

    // ==================== Public Methods 公开方法 ====================
    function collapse(sourceItem) {
        return transition._beginCapture(sourceItem, true)
    }

    function expand(sourceItem) {
        return transition._beginCapture(sourceItem, false)
    }

    function stop() {
        transition._captureGeneration += 1
        transition._capturePending = false
        transition._overlayFramePending = false
        transition._dissolving = false
        captureTimeout.stop()
        radiusTransition.stop()
        overlayWindow.visible = false
        transition._detach(true)
        transition._releaseSnapshot()
        transition._collapsed = false
    }

    // ==================== Internal Methods 内部方法 ====================
    function _attach(sourceItem) {
        if (!sourceItem) return false

        transition._sourceItem = sourceItem
        transition._savedVisible = sourceItem.visible
        transition._sourceStartX = sourceItem.x
        transition._sourceStartY = sourceItem.y
        sourceItem.visible = true
        return true
    }

    function _beginCapture(sourceItem, collapsing) {
        transition.stop()
        if (!transition._attach(sourceItem) || !transition._captureItem) {
            transition._completeWithoutAnimation(collapsing, "source item unavailable")
            return false
        }

        transition._captureGeneration += 1
        transition._capturePending = true
        transition._captureCollapsing = collapsing
        transition._collapsed = false
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
        transition._overlayFramePending = true
        frozenFrame.visible = true
        frozenFrame.opacity = Enums.opacityLevel.visible
        overlayWindow.visible = true
        overlayWindow.requestUpdate()
    }

    function _beginRadiusTransition() {
        if (!transition._capturePending || !transition._overlayFramePending) return

        transition._overlayFramePending = false
        transition._capturePending = false
        transition._dissolving = true
        if (transition._sourceItem) transition._sourceItem.visible = false
        radiusTransition.start(transition._captureCollapsing)
    }

    function _completeWithoutAnimation(collapsing, reason, expectedFallback) {
        if (expectedFallback) console.warn("LazyPageCircleTransition: " + reason)
        else console.error("LazyPageCircleTransition: " + reason)
        transition._capturePending = false
        transition._overlayFramePending = false
        transition._dissolving = false
        captureTimeout.stop()
        overlayWindow.visible = false
        var sourceItem = transition._sourceItem
        if (sourceItem) sourceItem.visible = !collapsing
        transition._detach(false)
        transition._releaseSnapshot()
        transition._collapsed = collapsing
        if (collapsing) transition.collapseFinished()
        else transition.expandFinished()
    }

    function _releaseSnapshot() {
        frozenFrame.source = ""
        transition._grabResult = null
    }

    function _detach(restoreVisibility) {
        var sourceItem = transition._sourceItem
        if (!sourceItem) return

        if (restoreVisibility) sourceItem.visible = transition._savedVisible
        transition._sourceItem = null
    }

    function _handleRadiusFinished() {
        var sourceItem = transition._sourceItem
        transition._dissolving = false
        overlayWindow.visible = false
        if (radiusTransition.collapsing) {
            if (sourceItem) sourceItem.visible = false
            transition._detach(false)
            transition._releaseSnapshot()
            transition._collapsed = true
            transition.collapseFinished()
            return
        }

        if (sourceItem) sourceItem.visible = true
        transition._detach(false)
        transition._releaseSnapshot()
        transition._collapsed = false
        transition.expandFinished()
    }

    visible: false
    Component.onDestruction: transition.stop()

    FeedbackInternal.QMLPageCircleTransition {
        id: radiusTransition

        objectName: "qmlPageCircleTransition"
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

    Window {
        id: overlayWindow

        objectName: "lazyPageCircleOverlayWindow"
        visible: false
        opacity: Enums.opacityLevel.visible
        color: Enums.transparent
        flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoFluentShadowWindowHint
        transientParent: null

        onFrameSwapped: transition._beginRadiusTransition()

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
            revealTarget: false
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
