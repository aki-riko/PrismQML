// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "_internal" as NavigationInternal
import "../.."

// PageTransition - Public page and splash transition facade 公开页面与启动画面过渡门面
//
// Custom Component contract 自定义 Component 合同:
// - methods: collapse(sourceItem), expand(sourceItem), stop()
// - state: active, running, collapsing, collapsed, progress
// - signals: collapseStarted, collapseFinished, expandStarted, expandFinished
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int animationType: Enums.lazyAnimation.lazy_circle
    property Component customAnimation: null
    property int revealDuration: Enums.lazyLoadingTransitionMetrics.revealDuration
    property int coverDuration: Enums.lazyLoadingTransitionMetrics.coverDuration
    property int revealEasing: Easing.OutQuint
    property int coverEasing: Easing.InOutQuad
    property bool revealTarget: false
    property bool keepSourceHiddenOnExpand: false
    property bool collapseToCenter: false
    // Animate in a separate clean window instead of masking inside the host. Needed when the
    // host has hwnd-level effects (DWM Mica, native shadow) that a QML mask cannot clip.
    // 在独立的干净窗口里做动画, 而不是在宿主内部遮罩。当宿主带有 QML 遮罩裁不到的 hwnd 级
    // 效果(DWM Mica、原生阴影)时需要它。
    property bool preferOverlayWindow: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool usingCustomAnimation: customAnimation !== null
    readonly property bool customAnimationContractValid: _contractValid
    readonly property bool running: _backend && _contractValid
        ? Boolean(_backend.running) : false
    readonly property bool active: _backend && _contractValid
        ? Boolean(_backend.active) : false
    readonly property bool collapsing: _backend && _contractValid
        ? Boolean(_backend.collapsing) : _operationCollapsing
    readonly property bool collapsed: _backend && _contractValid
        ? Boolean(_backend.collapsed) : _collapsed
    readonly property real progress: _backend && _contractValid
        ? Number(_backend.progress) : (_collapsed ? 1 : 0)
    readonly property real revealMinimumRadiusPixels: _backend && _contractValid
        ? Number(_backend.revealMinimumRadiusPixels) : 0
    readonly property real revealMaximumRadiusPixels: _backend && _contractValid
        ? Number(_backend.revealMaximumRadiusPixels) : 0
    readonly property real revealRadiusPixels: _backend && _contractValid
        ? Number(_backend.revealRadiusPixels) : 0
    readonly property bool _capturePending: _backend && _contractValid
        && typeof _backend._capturePending !== "undefined"
        ? Boolean(_backend._capturePending) : false
    readonly property int _overlayFrameStage: _backend && _contractValid
        && typeof _backend._overlayFrameStage !== "undefined"
        ? Number(_backend._overlayFrameStage) : 0
    readonly property bool _dissolving: _backend && _contractValid
        && typeof _backend._dissolving !== "undefined"
        ? Boolean(_backend._dissolving) : false
    readonly property bool _usingPageLayer: _backend && _contractValid
        && typeof _backend._usingPageLayer !== "undefined"
        ? Boolean(_backend._usingPageLayer) : false
    readonly property bool _inWindowStartPending: _backend && _contractValid
        && typeof _backend._inWindowStartPending !== "undefined"
        ? Boolean(_backend._inWindowStartPending) : false
    readonly property bool _mainFramePending: _backend && _contractValid
        && typeof _backend._mainFramePending !== "undefined"
        ? Boolean(_backend._mainFramePending) : false
    readonly property string _lastFallbackReason: _backend && _contractValid
        && typeof _backend._lastFallbackReason !== "undefined"
        ? String(_backend._lastFallbackReason) : ""

    // ==================== Internal Props 内部属性 ====================
    property var _backend: transitionLoader.item
    property bool _contractValid: false
    property bool _collapsed: false
    property bool _operationCollapsing: false
    property Item _sourceItem: null
    property bool _savedSourceVisible: false

    // ==================== Signals 信号 ====================
    signal collapseStarted()
    signal expandStarted()
    signal collapseFinished()
    signal expandFinished()

    // ==================== Public Methods 公开方法 ====================
    function collapse(sourceItem) {
        return _start(sourceItem, true)
    }

    function expand(sourceItem) {
        return _start(sourceItem, false)
    }

    // Undo the host-window hide from preferOverlayWindow. Safe to call unconditionally: it
    // is a no-op unless the backend actually hid the host.
    // 撤销 preferOverlayWindow 造成的宿主窗口隐藏。可以无条件调用: 除非后端真的藏了宿主,
    // 否则它什么都不做。
    function restoreHostWindow() {
        if (_backend && _contractValid
            && typeof _backend._restoreHostWindowAfterOverlay === "function")
            _backend._restoreHostWindowAfterOverlay()
    }

    function stop() {
        if (_backend && _contractValid && typeof _backend.stop === "function")
            _backend.stop()
        if (_sourceItem) _sourceItem.visible = _savedSourceVisible
        _sourceItem = null
        _savedSourceVisible = false
        _collapsed = false
        _operationCollapsing = false
    }

    // ==================== Internal Methods 内部方法 ====================
    function _hasRequiredContract(candidate) {
        if (!candidate) return false
        var methods = ["collapse", "expand", "stop"]
        var states = ["active", "running", "collapsing", "collapsed", "progress"]
        var signals = ["collapseStarted", "collapseFinished", "expandStarted", "expandFinished"]
        for (var methodIndex = 0; methodIndex < methods.length; methodIndex++) {
            if (typeof candidate[methods[methodIndex]] !== "function") return false
        }
        for (var stateIndex = 0; stateIndex < states.length; stateIndex++) {
            if (typeof candidate[states[stateIndex]] === "undefined") return false
        }
        for (var signalIndex = 0; signalIndex < signals.length; signalIndex++) {
            if (typeof candidate[signals[signalIndex]] !== "function") return false
        }
        return true
    }

    function _syncBackendContract(candidate) {
        _contractValid = _hasRequiredContract(candidate)
        if (usingCustomAnimation && !_contractValid) {
            console.error(
                "PageTransition: customAnimation must implement collapse/expand/stop " +
                "and active/running/collapsing/collapsed/progress")
        }
    }

    function _releaseCompletedSource() {
        _sourceItem = null
        _savedSourceVisible = false
    }

    function _completeWithoutAnimation(sourceItem, collapsing) {
        _operationCollapsing = collapsing
        if (sourceItem) sourceItem.visible = !collapsing
        _collapsed = collapsing
        if (collapsing) {
            collapseStarted()
            collapseFinished()
        } else {
            expandStarted()
            expandFinished()
        }
        _releaseCompletedSource()
    }

    function _start(sourceItem, collapsing) {
        stop()
        _sourceItem = sourceItem
        _savedSourceVisible = sourceItem ? sourceItem.visible : false
        _operationCollapsing = collapsing

        if (animationType === Enums.lazyAnimation.none ||
                (animationType !== Enums.lazyAnimation.lazy_circle &&
                 animationType !== Enums.lazyAnimation.cpu &&
                 animationType !== Enums.lazyAnimation.custom && !usingCustomAnimation)) {
            _completeWithoutAnimation(sourceItem, collapsing)
            return true
        }
        if (!_backend || !_contractValid) {
            console.error("PageTransition: transition backend contract is invalid")
            _completeWithoutAnimation(sourceItem, collapsing)
            return false
        }
        var methodName = collapsing ? "collapse" : "expand"
        return Boolean(_backend[methodName](sourceItem))
    }

    anchors.fill: parent

    // ==================== Content 内容 ====================
    Loader {
        id: transitionLoader

        objectName: "pageTransitionBackendLoader"
        anchors.fill: parent
        active: control.customAnimation !== null ||
                control.animationType === Enums.lazyAnimation.lazy_circle ||
                control.animationType === Enums.lazyAnimation.cpu
        asynchronous: false
        sourceComponent: control.customAnimation !== null
            ? control.customAnimation
            : (control.animationType === Enums.lazyAnimation.lazy_circle
                ? defaultTransitionComponent
                : (control.animationType === Enums.lazyAnimation.cpu
                    ? cpuTransitionComponent : null))
        onItemChanged: control._syncBackendContract(item)
    }

    Component {
        id: defaultTransitionComponent

        NavigationInternal.LazyPageCircleTransition {
            objectName: "qmlPageCircleTransition"
            revealDuration: control.revealDuration
            revealEasing: control.revealEasing
            coverDuration: control.coverDuration
            coverEasing: control.coverEasing
            revealTarget: control.revealTarget
            keepSourceHiddenOnExpand: control.keepSourceHiddenOnExpand
            collapseToCenter: control.collapseToCenter
            preferOverlayWindow: control.preferOverlayWindow
        }
    }

    Component {
        id: cpuTransitionComponent

        NavigationInternal.LazyPageCpuTransition {
            objectName: "qmlPageCpuTransition"
            revealDuration: control.revealDuration
            revealEasing: control.revealEasing
            coverDuration: control.coverDuration
            coverEasing: control.coverEasing
            revealTarget: control.revealTarget
            keepSourceHiddenOnExpand: control.keepSourceHiddenOnExpand
            collapseToCenter: control.collapseToCenter
            preferOverlayWindow: control.preferOverlayWindow
        }
    }

    Connections {
        function onCollapseStarted() { control.collapseStarted() }
        function onExpandStarted() { control.expandStarted() }
        function onCollapseFinished() {
            control._releaseCompletedSource()
            control.collapseFinished()
        }
        function onExpandFinished() {
            control._releaseCompletedSource()
            control.expandFinished()
        }

        target: control._backend
        ignoreUnknownSignals: true
    }
}
