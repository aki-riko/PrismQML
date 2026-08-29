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
        || _mainFramePending || _collapseFramePending || radiusTransition.running
    readonly property bool collapsing: radiusTransition.collapsing
    readonly property bool collapsed: _collapsed
    readonly property real progress: radiusTransition.progress
    readonly property var _hostWindow: transition.Window.window
    readonly property bool _hasLoaderItem: _sourceItem
        && typeof _sourceItem.item !== "undefined" && _sourceItem.item
    readonly property Item _captureItem: _hasLoaderItem
        ? _sourceItem.item
        : _sourceItem
    // Window close collapses to the center; page switches keep the navigation-sized
    // minimum so the wait indicator sits inside the remaining aperture.
    // 窗口关闭收紧到中心；页面切换保留导航栏大小的最小半径，让等待指示器落在剩余
    // 光圈内。
    readonly property real revealMinimumRadiusPixels:
        collapseToCenter && _captureCollapsing
            ? 0 : Enums.controlSize.navBarHeight / 2
    readonly property real revealMaximumRadiusPixels:
        Math.sqrt(width * width + height * height) * 0.5
        + Enums.lazyLoadingTransitionMetrics.edgeSoftness * 2
    readonly property real revealRadiusPixels:
        revealMinimumRadiusPixels
        + (revealMaximumRadiusPixels - revealMinimumRadiusPixels)
        * Math.max(0, Math.min(1, progress))

    // ==================== Public Props 公开属性 ====================
    property int revealDuration: Enums.lazyLoadingTransitionMetrics.revealDuration
    property int coverDuration: Enums.lazyLoadingTransitionMetrics.coverDuration
    // Forwarded to the radius animation; see QMLPageCircleTransition.
    // 转发给半径动画; 见 QMLPageCircleTransition。
    property int revealEasing: Easing.OutQuint
    property int coverEasing: Easing.InOutQuad
    property bool revealTarget: false
    // Keep external reveal sources hidden after expansion so the next window can show through.
    // 外部窗口揭幕后保持源项隐藏, 让后方窗口直接透出。
    property bool keepSourceHiddenOnExpand: false
    property bool collapseToCenter: false
    // Force the overlay window even when hosted in one; see _beginTransition.
    // 即使身处窗口内也强制走覆盖窗口; 见 _beginTransition。
    property bool preferOverlayWindow: false

    // ==================== Internal Props 内部属性 ====================
    property Item _sourceItem: null
    property bool _savedVisible: false
    property bool _collapsed: false
    property bool _capturePending: false
    property bool _captureCollapsing: false
    // Which capture path produced the current frame; decides whether an image load error
    // still has a fallback left. 当前帧出自哪条抓图路径; 决定图片加载失败时是否还有兜底。
    property bool _usingScreenCapture: false
    property bool _hostHiddenForOverlay: false
    property real _hostOpacityBeforeOverlay: Enums.opacityLevel.visible
    property int _overlayFrameStage: 0
    property bool _dissolving: false
    property bool _usingPageLayer: false
    property bool _inWindowStartPending: false
    property bool _mainFramePending: false
    property bool _collapseFramePending: false
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
        transition._collapseFramePending = false
        // Child ids may already be null when Component.onDestruction invokes stop().
        // Component.onDestruction 调用 stop() 时，子对象 id 可能已经为空。
        if (captureTimeout) captureTimeout.stop()
        if (mainFrameFallback) mainFrameFallback.stop()
        if (radiusTransition) radiusTransition.stop()
        if (overlayWindow) overlayWindow.visible = false
        transition._restoreHostWindowAfterOverlay()
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
        // The in-window page layer masks inside the host window, so hwnd-level effects
        // (DWM Mica, the native shadow) keep painting outside the mask — the mask cannot
        // reach them. The overlay window has neither (Qt.NoFluentShadowWindowHint, no
        // Mica), so there the QML mask is the only thing painting. Callers that need a
        // clean periphery must force it; _hostWindow is always set for a window-hosted
        // transition, so this branch would otherwise never be skipped.
        // 窗口内页面层是在宿主窗口里遮罩, 于是 hwnd 级效果(DWM Mica、原生阴影)照旧画在遮罩
        // 之外 —— 遮罩碰不到它们。覆盖窗口两者都没有(Qt.NoFluentShadowWindowHint、无 Mica),
        // 在那里 QML 遮罩是唯一作画的东西。需要干净外围的调用方必须强制走它; 窗口内的过渡
        // _hostWindow 恒有值, 否则这个分支永远不会被跳过。
        if (transition._hostWindow && !transition.preferOverlayWindow) {
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
        if (transition._captureFromScreen(generation)) return true
        return transition._captureWithItem(generation, collapsing)
    }

    // grabToImage only captures the QML scene graph. A window showing a DWM material does it
    // through a transparent windowColor, so the grab has a transparent background and the
    // overlay — which has no material of its own — renders the page see-through. A screen
    // grab reads back what DWM already composited, material included.
    // This is how the removed ripple close animation handled Mica (WindowCloseDissolve.qml,
    // deleted in 2445451bc); losing it with that file is what regressed.
    // grabToImage 只抓 QML 场景图。显示 DWM 材质的窗口是靠透明 windowColor 透出来的, 所以
    // 抓到的背景是透明的, 而覆盖窗自己没有材质, 页面就 render 成透视的。屏幕抓图读回的是
    // DWM 已经合成好的结果, 含材质。
    // 被移除的水波关闭动画就是这么处理 Mica 的(WindowCloseDissolve.qml, 于 2445451bc 删除);
    // 随那个文件一起丢掉它正是本次回归的原因。
    function _captureFromScreen(generation) {
        if (!transition.preferOverlayWindow) return false
        var host = transition._hostWindow
        var item = transition._captureItem
        if (!host || !item) return false
        if (typeof AcrylicHelper === "undefined" || !AcrylicHelper
                || typeof AcrylicHelper.grabWindowFrame !== "function") return false
        var source = AcrylicHelper.grabWindowFrame(
            host,
            Math.round(item.x),
            Math.round(item.y),
            Math.round(item.width),
            Math.round(item.height)
        )
        if (!source) return false
        if (!transition._capturePending
                || generation !== transition._captureGeneration) return false
        transition._grabResult = null
        transition._usingScreenCapture = true
        frozenFrame.source = source
        transition._showOverlayWhenReady()
        captureTimeout.restart()
        return true
    }

    function _captureWithItem(generation, collapsing) {
        transition._usingScreenCapture = false
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

    // Hiding the source item is not enough: the host window keeps its hwnd-level DWM Mica
    // and native shadow, which paint outside the overlay's mask and defeat the whole point
    // of moving to an overlay. Called only after the stage-2 mask frame is confirmed on
    // screen, so no frame has both windows invisible.
    // 只藏源项不够: 宿主窗口仍带着 hwnd 级的 DWM Mica 和原生阴影, 它们画在覆盖窗遮罩之外,
    // 会让搬到覆盖窗这件事完全失去意义。仅在阶段 2 遮罩帧确认上屏后调用, 故不存在两个窗口
    // 同时不可见的帧。
    function _hideHostWindowForOverlay() {
        if (!transition.preferOverlayWindow) return
        // Re-entering would save the already-zeroed opacity as the value to restore, leaving
        // the window permanently invisible. 重入会把已归零的不透明度存成待还原值, 窗口就永久
        // 不可见了。
        if (transition._hostHiddenForOverlay) return
        var host = transition._hostWindow
        if (!host) return
        // opacity, not visible: visible=false tears down the scene graph, which stops the
        // animation that is still driving the overlay.
        // 用 opacity 而非 visible: visible=false 会拆掉场景图, 而那个场景图还在驱动覆盖窗的
        // 动画。
        transition._hostOpacityBeforeOverlay = host.opacity
        transition._hostHiddenForOverlay = true
        host.opacity = Enums.opacityLevel.invisible
    }

    function _restoreHostWindowAfterOverlay() {
        if (!transition._hostHiddenForOverlay) return
        transition._hostHiddenForOverlay = false
        var host = transition._hostWindow
        if (host) host.opacity = transition._hostOpacityBeforeOverlay
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
            transition._hideHostWindowForOverlay()
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
        transition._collapseFramePending = false
        captureTimeout.stop()
        overlayWindow.visible = false
        transition._restoreHostWindowAfterOverlay()
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
        transition._usingScreenCapture = false
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
            // Let the zero-radius shader frame render before removing its source.
            // 先让半径归零的 shader 帧完成渲染,再移除源项。
            transition._collapseFramePending = true
            if (transition._hostWindow) transition._hostWindow.requestUpdate()
            else overlayWindow.requestUpdate()
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
        transition._collapseFramePending = false
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

    function _handleCollapseFrameEnd() {
        if (transition._collapseFramePending)
            transition._finalizeCollapse()
    }

    visible: false
    Component.onDestruction: transition.stop()

    FeedbackInternal.QMLPageCircleTransition {
        id: radiusTransition

        objectName: "qmlPageCircleTransition"
        revealDuration: transition.revealDuration
        revealEasing: transition.revealEasing
        coverDuration: transition.coverDuration
        coverEasing: transition.coverEasing
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
            minimumRadiusPixels: transition.revealMinimumRadiusPixels
            progress: radiusTransition.progress
            revealTarget: transition.revealTarget
        }
    }

    Connections {
        target: transition._hostWindow

        function onFrameSwapped() { transition._handleSourceWindowFrameSwapped() }
        function onAfterFrameEnd() { transition._handleCollapseFrameEnd() }
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
        onAfterFrameEnd: transition._handleCollapseFrameEnd()

        FeedbackInternal.QMLPageCircleFrame {
            id: circleFrame

            objectName: "lazyPageCircleFrame"
            minimumRadiusPixels: transition.revealMinimumRadiusPixels
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
                    // A screen grab that fails to load still has the item grab left to try;
                    // only give up on the animation once that path fails too.
                    // 屏幕抓图加载失败时还剩下抓取项这条路可试; 只有那条也失败才放弃动画。
                    if (transition._usingScreenCapture) {
                        transition._usingScreenCapture = false
                        transition._captureWithItem(
                            transition._captureGeneration, transition._captureCollapsing)
                        return
                    }
                    transition._completeWithoutAnimation(
                        transition._captureCollapsing, "snapshot image load failed")
                }
            }
        }

    }
}
