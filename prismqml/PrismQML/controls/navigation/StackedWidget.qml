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
            "animationType": control.animationType,
            "animationDuration": control.animationDuration,
            "loaderActivationDelay": control.lazyActivationDelay,
            "popUpOffset": control.popUpOffset,
            "isPageLoadedFunc": control._isPageLoaded,
            "isPageLoadFailedFunc": control._isPageLoadFailedFunc,
            "pageLoadErrorFunc": control._pageLoadErrorFunc,
            "activateLoaderFunc": control._activateLoader,
            "diagnosticFunc": control._traceLazyStage
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
        if (!control.lazyLoading || !_isPageLoaded(_displayIndex)) return
        _ensureLazyHelperLoaded(reason)
    }

    function _showLazyLoadingAndSwitch(index) {
        _traceLazyStage("stacked.switch_request", index)
        _pendingLazySwitchIndex = index
        _ensureLazyHelperLoaded("switch target=" + index)
        if (!lazyHelperLoader.item) return
        if (!lazyHelperLoader.active) {
            lazyHelperLoader.active = true
            profileTime("lazyHelper deferred load reactivated target=" + index)
            return
        }
        _flushPendingLazySwitch()
    }

    function _flushPendingLazySwitch() {
        if (_pendingLazySwitchIndex < 0) return
        if (!lazyHelperLoader.item) return

        var target = _pendingLazySwitchIndex
        _pendingLazySwitchIndex = -1
        _traceLazyStage("stacked.helper_dispatch.begin", target)
        lazyHelperLoader.item.showLoadingAndSwitch(target)
        _traceLazyStage("stacked.helper_dispatch.done", target)
    }

    function _configureLazyHelper(item) {
        if (!item) return

        item.width = Qt.binding(function() { return lazyHelperLoader.width })
        item.height = Qt.binding(function() { return lazyHelperLoader.height })
        item.loaders = Qt.binding(function() { return control._loaders })
        item.targetIndex = Qt.binding(function() { return control.currentIndex })
        item.currentVisibleIndex = Qt.binding(function() { return control._displayIndex })
        item.loadingText = Qt.binding(function() { return control.loadingText })
        item.loaderActivationDelay = Qt.binding(function() { return control.lazyActivationDelay })
        item.isPageLoadedFunc = control._isPageLoaded
        item.isPageLoadFailedFunc = control._isPageLoadFailedFunc
        item.pageLoadErrorFunc = control._pageLoadErrorFunc
        item.activateLoaderFunc = control._activateLoader
        item.diagnosticFunc = control._traceLazyStage
        item.loadingComplete.connect(control._handleLazyLoadingComplete)
        item.loadingFailed.connect(function(targetIdx, errorString) {
            control._traceLazyStage("stacked.loading_failed", targetIdx)
            control.profileTime(
                "lazyHelper loadingFailed target=" + targetIdx + ", error=" + errorString)
            control.pageLoadFailed(targetIdx, errorString)
        })
    }

    function _completePythonLazySwitch(targetIndex) {
        if (targetIndex < 0 || targetIndex >= count || targetIndex !== currentIndex) {
            return false
        }
        if (!animations.prepareEnter(targetIndex)) return false
        _doEnterAnimation(targetIndex)
        return true
    }

    function _handleLazyLoadingComplete(targetIdx, prevIdx) {
        control._traceLazyStage("stacked.loading_complete.begin", targetIdx,
                                "previous=" + prevIdx)
        control.profileTime("lazyHelper loadingComplete start target=" + targetIdx + ", prev=" + prevIdx)
        // 更新实际显示页(不写 currentIndex: 它已是 targetIdx 且不能命令式写,
        // 否则打破外部 'currentIndex: window.currentIndex' 绑定)。
        control.previousIndex = control._displayIndex
        control._displayIndex = targetIdx
        if (animations.prepareEnter(targetIdx)) {
            control._doEnterAnimation(targetIdx)
        }
        control.profileTime("lazyHelper loadingComplete done")
        control._traceLazyStage("stacked.loading_complete.done", targetIdx,
                                "previous=" + prevIdx)
    }

    // Animation execution 动画执行
    function _doAnimation(oldIndex, newIndex) {
        var oldW = widget(oldIndex)
        var newW = widget(newIndex)
        _hideAllExcept([oldIndex, newIndex])

        if (!animationEnabled || animationType === Enums.animation.none) {
            _updateVisibility(newIndex)
            currentChanged(newIndex)
            return
        }

        var isBack = newIndex < oldIndex

        switch (animationType) {
            case Enums.animation.opacity:
                animations.fadeTransition(oldIndex, newIndex)
                break
            case Enums.animation.popup:
                animations.popUpTransition(oldIndex, newIndex)
                break
            case Enums.animation.popdown:
                animations.popDownTransition(oldIndex, newIndex)
                break
            case Enums.animation.slide:
                animations.slideTransition(oldIndex, newIndex, isBack)
                break
            case Enums.animation.card:
                animations.cardTransition(oldIndex, newIndex, isBack)
                break
            case Enums.animation.zoom:
                animations.zoomTransition(oldIndex, newIndex)
                break
            default:
                animations.fadeTransition(oldIndex, newIndex)
        }

        animationStarted()
    }
    function _hideAllExcept(exceptIndices) {
        if (_destroying) return
        if (_useSourceMode) {
            for (var i = 0; i < _loaders.length; i++) {
                var loader = _loaders[i]
                if (loader && exceptIndices.indexOf(i) === -1) {
                    // Each assignment may synchronously destroy a Loader through bindings.
                    // 每次赋值都可能通过绑定同步销毁 Loader，因此逐项重验引用。
                    loader.visible = false
                    if (!loader) continue
                    loader.opacity = 0
                    if (!loader) continue
                    loader.y = 0
                    if (!loader) continue
                    loader.x = 0
                    if (!loader) continue
                    loader.scale = 1
                }
            }
        } else {
            for (var j = 0; j < stackLayout.children.length; j++) {
                if (exceptIndices.indexOf(j) === -1) {
                    var child = stackLayout.children[j]
                    child.visible = false
                    child.opacity = 0
                    child.y = 0
                    child.x = 0
                    child.scale = 1
                }
            }
        }
    }

    function _doEnterAnimation(newIndex) {
        _hideAllExcept([newIndex])

        if (!animationEnabled || animationType === Enums.animation.none) {
            _updateVisibility(newIndex)
            currentChanged(newIndex)
            return
        }

        switch (animationType) {
            case Enums.animation.opacity:
                animations.enterFadeOnly(newIndex)
                break
            case Enums.animation.popup:
                animations.enterPopUpOnly(newIndex)
                break
            case Enums.animation.popdown:
                animations.enterPopDownOnly(newIndex)
                break
            case Enums.animation.zoom:
                animations.enterZoomOnly(newIndex)
                break
            case Enums.animation.slide:
            case Enums.animation.card:
                animations.enterSlideOnly(newIndex)
                break
            default:
                animations.enterFadeOnly(newIndex)
        }
        animationStarted()
    }

    function _updateVisibility(newIndex) {
        if (_useSourceMode) {
            for (var i = 0; i < _loaders.length; i++) {
                if (_loaders[i]) {
                    var isCurrent = (i === newIndex)
                    _loaders[i].visible = isCurrent
                    _loaders[i].opacity = isCurrent ? 1 : 0
                }
            }
        } else {
            for (var j = 0; j < stackLayout.children.length; j++) {
                var child = stackLayout.children[j]
                child.visible = (j === newIndex)
                child.opacity = (j === newIndex) ? 1 : 0
            }
        }
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

    onLazyLoadingChanged: if (lazyLoading) _preloadLazyHelperWhenReady("lazyLoadingChanged")
    onPageLoaded: (index) => {
        if (index === _displayIndex) _preloadLazyHelperWhenReady("pageLoaded index=" + index)
    }
    onCurrentIndexChanged: {
        _traceLazyStage("stacked.current_index_changed", currentIndex)
        profileTime("currentIndex changed to " + currentIndex)
        // currentIndex 是目标页(外部输入)。用 _displayIndex(实际显示页)判重,
        // 内部绝不回写 currentIndex(否则打破外部声明式绑定)。
        if (currentIndex === _displayIndex) return
        if (currentIndex < 0 || currentIndex >= count) return

        // QML pageSources 懒加载模式：使用 LazyLoadingHelper。
        if (lazyLoading && !_isPageLoaded(currentIndex)) {
            // 不回退 currentIndex: 旧页靠 _displayIndex(仍为旧值)保持可见,
            // loading 完成后由 LazyLoadingHelper.onLoadingComplete 更新 _displayIndex。
            _showLazyLoadingAndSwitch(currentIndex)
        } else {
            // Normal switch or Python mode 正常切换或Python模式
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
    Item {
        id: sourceContainer
        anchors.fill: parent
        visible: control._useSourceMode
        
        Repeater {
            id: sourceRepeater
            model: control._useSourceMode ? control._safePageSources.length : 0
            
            Loader {
                id: sourceLoader

                property bool _loadOnce: false
                property int pageIndex: index

                width: sourceContainer.width
                height: sourceContainer.height
                // latch 用独立布尔 _loadOnce, 不自引用 active(自引用——含绕 _loaders[index]
                // 间接自引用——会因 Loader.active 默认 true / _loaders 数组 slice 重建触发
                // 连锁, 导致所有页一启动就 active 全加载, 懒加载失效)。
                // _loadOnce 初始 false → 初始 active 仅跟 index===_displayIndex(只当前页);
                // 页面一旦被激活 onActiveChanged 锁 _loadOnce=true, 切走再切回仍 active,
                // source 不清空(避免 status===Ready latch 的切走退出 Ready→source 清空→永久轮询死锁)。
                onActiveChanged: {
                    if (active) _loadOnce = true
                    control._traceLazyStage(
                        "stacked.source_loader.active_changed", index, "", sourceLoader)
                }
                onStatusChanged: control._traceLazyStage(
                    "stacked.source_loader.status_changed", index, "", sourceLoader)
                source: control.lazyLoading
                        ? (index === control._displayIndex || _loadOnce
                           ? (control._safePageSources[index] || "") : "")
                        : (control._safePageSources[index] || "")
                active: !control.lazyLoading || index === control._displayIndex || _loadOnce
                visible: index === control._displayIndex
                opacity: index === control._displayIndex ? 1 : 0
                scale: 1
                transformOrigin: Item.Center
                asynchronous: control.lazyLoading && control._asynchronousPageLoaderEnabled
                
                Component.onCompleted: {
                    var loaders = control._loaders.slice()
                    loaders[index] = sourceLoader
                    control._loaders = loaders
                    control.profileTime("sourceLoader registered index=" + index)
                }
                Component.onDestruction: {
                    if (!control || control._destroying) return
                    var loaders = control._loaders.slice()
                    var registeredIndex = pageIndex
                    if (registeredIndex >= 0 && loaders[registeredIndex] === sourceLoader) {
                        loaders[registeredIndex] = null
                        while (loaders.length > 0 && !loaders[loaders.length - 1]) loaders.pop()
                        control._loaders = loaders
                    }
                }

                // latch on actual load completion 加载完成即合锁。
                // 初始当前页(主页)启动时 active 默认即 true, 绑定算出 true 但值未发生
                // 变化 → onActiveChanged 不触发 → _loadOnce 漏锁 → 切走被卸载、切回重新
                // 懒加载。onLoaded 是"已加载"的权威信号, 主页启动会触发, 在此补锁兜底。
                onLoaded: {
                    control._traceLazyStage(
                        "stacked.source_loader.loaded.begin", index, "", sourceLoader)
                    _loadOnce = true
                    control.pageLoaded(index)
                    control.profileTime("sourceLoader onLoaded index=" + index)
                    control._traceLazyStage(
                        "stacked.source_loader.loaded.done", index, "", sourceLoader)
                }
            }
        }
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
}
