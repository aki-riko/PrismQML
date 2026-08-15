// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal"

// StackedWidget - Unified stacked page switch component 统一堆叠页面组件
// Supports: Multiple animations 支持多种动画
// Animation types: None/Opacity/PopUp/PopDown/Slide/Card/Zoom 动画类型
// Note: Lazy loading is handled by Python side, QML only provides animation 注意：懒加载由 Python 侧处理，QML 只提供动画能力
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int currentIndex: 0
    property int animationType: Enums.animation.opacity
    property int animationDuration: Enums.duration.slow
    // Extra delay before Loader activation, used to let navigation feedback settle
    // Loader 激活前的额外延迟，用于等待导航反馈动画稳定
    property int lazyActivationDelay: Enums.duration.none
    property bool animationEnabled: true
    property real cardScale: Enums.opacityLevel.heavy
    property real cardOpacity: Enums.opacityLevel.heavy
    property int popUpOffset: Enums.controlSize.popUpOffset
    
    // QML lazy-loading props for pure QML usage 纯QML使用的懒加载属性
    property bool lazyLoading: false
    property var pageSources: []  // QML file paths QML文件路径列表
    property string loadingText: { Translator._v; return Translator.tr("loading") }
    property var _loaders: []
    readonly property real _startupProfileStart: Date.now()
    property real _startupProfileLast: _startupProfileStart
    readonly property bool _startupProfilingVerboseActive:
        (typeof PrismQmlStartupProfileVerbose !== "undefined" && PrismQmlStartupProfileVerbose)
    readonly property bool _asynchronousPageLoaderEnabled:
        typeof PrismQmlAsynchronousPageLoaderEnabled === "undefined" ||
        PrismQmlAsynchronousPageLoaderEnabled
    property var _isPageLoadFailedFunc: function(index) {
        if (!lazyLoading || !_useSourceMode) return false
        return _loaders[index] && _loaders[index].status === Loader.Error
    }
    property var _pageLoadErrorFunc: function(index) {
        var loader = _loaders[index]
        if (!loader || loader.status !== Loader.Error) return ""
        if (loader.sourceComponent) {
            return String(loader.sourceComponent.errorString())
        }
        return String(loader.source)
    }
    
    readonly property var _safePageSources:
        pageSources === null || pageSources === undefined ? []
        : (typeof pageSources.length === "number" ? pageSources : [])
    readonly property bool _useSourceMode: _safePageSources.length > 0
    property int count: _useSourceMode ? _safePageSources.length : stackLayout.children.length

    // ==================== Internal Props 内部属性 ====================
    property bool _destroying: false
    default property alias content: stackLayout.children
    property alias containerItem: stackLayout
    property Item currentWidget: _getCurrentWidget()
    property int previousIndex: 0
    property int _displayIndex: 0
    property int _pendingLazySwitchIndex: -1
    property int _lazyDiagnosticSequence: 0
    property int _pythonLazyTransitionTargetIndex: -1
    property bool _pythonLazyRevealRequested: false
    // Python-managed windows must explicitly acknowledge page readiness.
    // Python 页面由宿主生命周期确认就绪，不能把“容器已创建”当成首屏已完成。
    property bool _pythonPageMode: false
    property var _pythonReadyIndexes: []

    // ==================== Signals 信号 ====================
    signal currentChanged(int index)
    signal animationFinished()
    signal animationStarted()
    signal pageLoaded(int index)
    signal pageLoadFailed(int index, string errorString)
    signal pythonLazyCollapseFinished(int index)
    signal pythonLazyExpansionStarted(int index)
    signal pythonLazyTransitionFinished(int index)

    function _getCurrentWidget() {
        if (_displayIndex < 0 || _displayIndex >= count) return null
        if (_useSourceMode && _loaders[_displayIndex]) {
            return _loaders[_displayIndex]
        }
        return stackLayout.children[_displayIndex]
    }
    function profileTime(msg) {
        if (!_startupProfilingVerboseActive) return
        var now = Date.now()
        console.debug("[启动剖析] StackedWidget " + msg + ": +" +
                    Math.round(now - _startupProfileLast) + "ms / total " +
                    Math.round(now - _startupProfileStart) + "ms")
        _startupProfileLast = now
    }

    function _loaderDiagnosticSnapshot(index, loaderOverride) {
        var loader = loaderOverride ||
                (index >= 0 && index < _loaders.length ? _loaders[index] : null)
        var targetSource = index >= 0 && index < _safePageSources.length ?
                    String(_safePageSources[index]) : ""
        var currentSource = _displayIndex >= 0 && _displayIndex < _safePageSources.length ?
                    String(_safePageSources[_displayIndex]) : ""
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

    function _traceLazyStage(stage, index, details, loaderOverride) {
        if (!_startupProfilingVerboseActive) return
        _lazyDiagnosticSequence += 1
        var detailText = details ? " " + details : ""
        console.debug("[懒加载诊断] StackedWidget #" + _lazyDiagnosticSequence +
                    " stage=" + stage +
                    " target=" + index +
                    " current=" + currentIndex +
                    " display=" + _displayIndex +
                    " pending=" + _pendingLazySwitchIndex + " " +
                    _loaderDiagnosticSnapshot(index, loaderOverride) + detailText)
    }

    // ==================== Internal Methods 内部方法 ====================
    function _isPageLoaded(index) {
        if (_pythonPageMode) {
            return count === 0 || _pythonReadyIndexes.indexOf(index) >= 0
        }
        if (!lazyLoading && _useSourceMode && !eagerActivationHelper.ready) {
            return eagerActivationHelper.isPageLoaded(index)
        }
        if (!lazyLoading || !_useSourceMode) return true
        return _loaders[index] && _loaders[index].status === Loader.Ready
    }

    function _markPythonPageReady(index) {
        if (!_pythonPageMode || index < 0) return
        if (_pythonReadyIndexes.indexOf(index) < 0) {
            var readyIndexes = _pythonReadyIndexes.slice()
            readyIndexes.push(index)
            _pythonReadyIndexes = readyIndexes
        }
        pageLoaded(index)
    }

    function _activateLoader(index) {
        _traceLazyStage("stacked.loader_activate.begin", index)
        if (_loaders[index] && !_loaders[index].active) {
            if (_useSourceMode) {
                _loaders[index].source = _safePageSources[index] || ""
            }
            _loaders[index].active = true
        }
        _traceLazyStage("stacked.loader_activate.done", index)
    }

    function _lazyHelperInitialProperties() {
        return {
            "loaders": control._loaders,
            "targetIndex": control.currentIndex,
            "currentVisibleIndex": control._displayIndex,
            "loadingText": control.loadingText,
            "loaderActivationDelay": control.lazyActivationDelay,
            "isPageLoadedFunc": control._isPageLoaded,
            "isPageLoadFailedFunc": control._isPageLoadFailedFunc,
            "pageLoadErrorFunc": control._pageLoadErrorFunc,
            "activateLoaderFunc": control._activateLoader,
            "diagnosticFunc": control._traceLazyStage,
            "pageTransition": pageCircleTransition
        }
    }

    function _ensureLazyHelperLoaded(reason) {
        if (!control.lazyLoading || !control._useSourceMode ||
                lazyHelperLoader.item || lazyHelperLoader.status !== Loader.Null) return

        _traceLazyStage("stacked.helper_load.begin", currentIndex,
                        "reason=" + reason, lazyHelperLoader)
        lazyHelperLoader.active = true
        lazyHelperLoader.setSource(Qt.resolvedUrl("_internal/LazyLoadingHelper.qml"), _lazyHelperInitialProperties())
        profileTime("lazyHelper preload requested reason=" + reason)
        _traceLazyStage("stacked.helper_load.done", currentIndex,
                        "reason=" + reason, lazyHelperLoader)
    }

    function _preloadLazyHelperWhenReady(reason) {
        lazyController.preloadLazyHelperWhenReady(reason)
    }

    function _cancelPendingLazySwitch(reason) {
        return lazyController.cancelPendingLazySwitch(reason)
    }

    function _showLazyLoadingAndSwitch(index) {
        lazyController.showLazyLoadingAndSwitch(index)
    }

    function _flushPendingLazySwitch() {
        lazyController.flushPendingLazySwitch()
    }

    function _configureLazyHelper(item) {
        lazyController.configureLazyHelper(item)
    }

    function _beginPythonLazySwitch(targetIndex) {
        return lazyController.beginPythonLazySwitch(targetIndex)
    }

    function _startPythonLazyExpansion(targetIndex) {
        lazyController.startPythonLazyExpansion(targetIndex)
    }

    function _cancelPythonLazySwitch(targetIndex) {
        lazyController.cancelPythonLazySwitch(targetIndex)
    }

    function _completePythonLazySwitch(targetIndex) {
        return lazyController.completePythonLazySwitch(targetIndex)
    }

    function _handlePythonLazyCollapseFinished() {
        lazyController.handlePythonLazyCollapseFinished()
    }

    function _handlePythonLazyExpandStarted() {
        lazyController.handlePythonLazyExpandStarted()
    }

    function _handlePythonLazyExpandFinished() {
        lazyController.handlePythonLazyExpandFinished()
    }

    function _handleLazyLoadingComplete(targetIdx, prevIdx) {
        lazyController.handleLazyLoadingComplete(targetIdx, prevIdx)
    }

    // Animation execution 动画执行
    function _doAnimation(oldIndex, newIndex) {
        visibilityController.doAnimation(oldIndex, newIndex)
    }

    function _hideAllExcept(exceptIndices) {
        visibilityController.hideAllExcept(exceptIndices)
    }

    function _doEnterAnimation(newIndex) {
        visibilityController.doEnterAnimation(newIndex)
    }

    function _updateVisibility(newIndex) {
        visibilityController.updateVisibility(newIndex)
    }
    // Get current index 获取当前索引
    function getCurrentIndex() {
        return currentIndex
    }

    // ==================== Public Methods 公开方法 ====================
    function setCurrentIndex(index, isBack) {
        if (index < 0 || index >= count || index === currentIndex) return
        currentIndex = index
    }

    function setCurrentWidget(w) {
        for (var i = 0; i < count; i++) {
            var item = widget(i)
            if (item === w) {
                setCurrentIndex(i)
                return
            }
        }
    }

    function widget(index) {
        if (index < 0 || index >= count) return null
        if (_useSourceMode) {
            return _loaders[index] || null
        }
        return stackLayout.children[index]
    }

    function next() {
        if (currentIndex < count - 1) setCurrentIndex(currentIndex + 1)
    }

    function previous() {
        if (currentIndex > 0) setCurrentIndex(currentIndex - 1)
    }

    function indexOf(item) {
        if (_useSourceMode) {
            for (var i = 0; i < _loaders.length; i++) {
                if (_loaders[i] && _loaders[i].item === item) return i
            }
        } else {
            for (var j = 0; j < stackLayout.children.length; j++) {
                if (stackLayout.children[j] === item) return j
            }
        }
        return -1
    }

    function itemAt(index) {
        return widget(index)
    }

    clip: true

    Component.onCompleted: {
        profileTime("Component.onCompleted count=" + count +
                    ", lazyLoading=" + lazyLoading +
                    ", sourceMode=" + _useSourceMode)
        _preloadLazyHelperWhenReady("completed")
    }
    Component.onDestruction: _destroying = true

    onLazyLoadingChanged: {
        if (lazyLoading) {
            eagerActivationHelper.cancel()
            _preloadLazyHelperWhenReady("lazyLoadingChanged")
        } else {
            eagerActivationHelper.start()
        }
    }
    onPageLoaded: (index) => {
        if (index === _displayIndex) _preloadLazyHelperWhenReady("pageLoaded index=" + index)
        if (!lazyLoading && index === eagerActivationHelper.requestedIndex &&
                index !== _displayIndex && index === currentIndex) {
            eagerActivationHelper.requestedIndex = -1
            previousIndex = _displayIndex
            _doAnimation(_displayIndex, index)
            _displayIndex = index
        }
    }
    onCurrentIndexChanged: {
        _traceLazyStage("stacked.current_index_changed", currentIndex)
        profileTime("currentIndex changed to " + currentIndex)
        // currentIndex 是目标页(外部输入)。用 _displayIndex(实际显示页)判重,
        // 内部绝不回写 currentIndex(否则打破外部声明式绑定)。
        if (currentIndex === _displayIndex) {
            _cancelPendingLazySwitch("returned-to-visible")
            return
        }
        if (currentIndex < 0 || currentIndex >= count) return

        var helper = lazyHelperLoader.item
        if (helper && helper.pendingTargetIndex >= 0
                && helper.pendingTargetIndex !== currentIndex) {
            _cancelPendingLazySwitch("retargeted")
        }

        if (lazyLoading && !_isPageLoaded(currentIndex)) {
            if (!_pythonPageMode) {
                // QML pageSources lazy mode is owned by LazyLoadingHelper.
                // QML pageSources 懒加载模式由 LazyLoadingHelper 管理。
                _showLazyLoadingAndSwitch(currentIndex)
            }
            // Python mode starts its circle transition from _startPythonLoading().
            // Python 模式由 _startPythonLoading() 启动圆形过渡，此处保持旧页显示。
        } else if (!lazyLoading && _useSourceMode && !_isPageLoaded(currentIndex)) {
            eagerActivationHelper.request(currentIndex)
        } else {
            // Loaded pages always use the configured StackedWidget transition.
            // 已加载页面始终使用 StackedWidget 配置的常规切页动画。
            previousIndex = _displayIndex
            _doAnimation(_displayIndex, currentIndex)
            _displayIndex = currentIndex
        }
    }

    // ==================== Content 内容 ====================
    // Animation helper 动画助手
    StackedModeAnimations {
        id: animations
        control: control
        animationDuration: control.animationDuration
        cardScale: control.cardScale
        cardOpacity: control.cardOpacity
        onAnimationFinished: (idx) => {
            control.currentChanged(idx)
            control.animationFinished()
        }
    }

    EagerLoadingHelper {
        id: eagerActivationHelper

        objectName: "eagerActivationHelper"
        loaders: control._loaders
        count: control.count
        lazyLoading: control.lazyLoading
        sourceMode: control._useSourceMode
    }

    LazyPageCircleTransition {
        id: pageCircleTransition

        objectName: "lazyPageCircleTransition"
        anchors.fill: parent
        onExpandStarted: control._handlePythonLazyExpandStarted()
        onCollapseFinished: control._handlePythonLazyCollapseFinished()
        onExpandFinished: control._handlePythonLazyExpandFinished()
    }

    // Direct children container 直接子组件容器
    Item {
        id: stackLayout
        objectName: "stackLayout"
        anchors.fill: parent
        visible: !control._useSourceMode
        
        Component.onCompleted: {
            control.profileTime("stackLayout Component.onCompleted start children=" + children.length)
            for (let i = 0; i < children.length; i++) {
                let child = children[i]
                child.width = Qt.binding(function() { return stackLayout.width })
                child.height = Qt.binding(function() { return stackLayout.height })
                child.x = 0
                child.y = 0
                child.visible = (i === control._displayIndex)
                child.opacity = (i === control._displayIndex) ? 1 : 0
                child.scale = 1
                child.transformOrigin = Item.Center
            }
            control.profileTime("stackLayout Component.onCompleted done")
        }
    }
    // pageSources mode 文件路径模式
    StackedSourcePages {
        id: sourcePages
        anchors.fill: parent
        host: control
        eagerHelper: eagerActivationHelper
    }
    
    // QML lazy-loading helper for pure QML usage 纯QML使用的懒加载辅助器
    Loader {
        id: lazyHelperLoader
        anchors.fill: parent
        active: false
        asynchronous: control._asynchronousPageLoaderEnabled
        onActiveChanged: control._traceLazyStage(
            "stacked.helper_loader.active_changed", control.currentIndex,
            "", lazyHelperLoader)
        onStatusChanged: control._traceLazyStage(
            "stacked.helper_loader.status_changed", control.currentIndex,
            "", lazyHelperLoader)
        onLoaded: {
            control._traceLazyStage(
                "stacked.helper_loader.loaded.begin", control.currentIndex,
                "", lazyHelperLoader)
            control._configureLazyHelper(item)
            control.profileTime("lazyHelper loaded")
            control._flushPendingLazySwitch()
            control._traceLazyStage(
                "stacked.helper_loader.loaded.done", control.currentIndex,
                "", lazyHelperLoader)
        }
    }

    // Lazy switch orchestration 懒切换编排
    StackedLazyController {
        id: lazyController
        host: control
        lazyHelperLoader: lazyHelperLoader
        pageTransition: pageCircleTransition
        animations: animations
    }

    // Visibility and animation orchestration 可见性与动画编排
    StackedVisibilityController {
        id: visibilityController
        host: control
        animations: animations
        container: stackLayout
    }
}
