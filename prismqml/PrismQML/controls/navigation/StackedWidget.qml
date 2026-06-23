// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
    property bool animationEnabled: true
    property real cardScale: Enums.opacityLevel.heavy
    property real cardOpacity: Enums.opacityLevel.heavy
    property int popUpOffset: Enums.controlSize.popUpOffset
    
    // ==================== QML Lazy Loading Props (for pure QML usage) QML懒加载属性（纯QML使用） ====================
    property bool lazyLoading: false
    property list<Component> pageComponents: []  // Legacy: Component list 旧版：组件列表
    property var pageSources: []                 // New: QML file paths 新版：QML文件路径列表
    property string loadingText: Translator.tr("loading")
    property var _loaders: []
    
    // Use pageSources if provided, otherwise fall back to pageComponents 优先使用 pageSources，否则回退到 pageComponents

    readonly property bool _useSourceMode: pageSources.length > 0
    
    // ==================== Signals 信号 ====================
    signal currentChanged(int index)
    signal animationFinished()
    signal animationStarted()
    signal pageLoaded(int index)
    
    // ==================== Internal Props 内部属性 ====================
    default property alias content: stackLayout.children
    property alias containerItem: stackLayout
    property int count: _useSourceMode ? pageSources.length : (pageComponents.length > 0 ? pageComponents.length : stackLayout.children.length)
    property Item currentWidget: _getCurrentWidget()
    property int previousIndex: 0
    // 实际显示页(唯一真相源, 驱动可见性/动画/当前 widget)。
    // currentIndex 是外部输入(目标页), 内部永不命令式写它(避免打破外部
    // 'currentIndex: window.currentIndex' 绑定); 真正"显示哪页"由 _displayIndex
    // 决定, 懒加载完成或动画切换时才更新, 实现"目标页先加载、加载完再显示"。
    property int _displayIndex: 0

    clip: true

    function _getCurrentWidget() {
        if (_displayIndex < 0 || _displayIndex >= count) return null
        if ((_useSourceMode || pageComponents.length > 0) && _loaders[_displayIndex]) {
            return _loaders[_displayIndex]
        }
        return stackLayout.children[_displayIndex]
    }

    // ==================== Lazy Loading Functions 懒加载函数 ====================
    function _isPageLoaded(index) {
        if (!lazyLoading) return true
        return _loaders[index] && _loaders[index].status === Loader.Ready
    }

    function _activateLoader(index) {
        if (_loaders[index] && !_loaders[index].active) {
            if (_useSourceMode) {
                _loaders[index].source = pageSources[index] || ""
            }
            _loaders[index].active = true
        }
    }

    // ==================== Animation Execution 动画执行 ====================
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
        if (_useSourceMode || pageComponents.length > 0) {
            for (var i = 0; i < _loaders.length; i++) {
                if (_loaders[i] && exceptIndices.indexOf(i) === -1) {
                    _loaders[i].visible = false
                    _loaders[i].opacity = 0
                    _loaders[i].y = 0
                    _loaders[i].x = 0
                    _loaders[i].scale = 1
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
        if (_useSourceMode || pageComponents.length > 0) {
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
    // ==================== Public Methods 公共方法 ====================

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
        if (_useSourceMode || pageComponents.length > 0) {
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
        if (_useSourceMode || pageComponents.length > 0) {
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

    // ==================== Animation Helper 动画助手 ====================
    StackedAnimations {
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

    // ==================== Direct Children Container 直接子组件容器 ====================
    Item {
        id: stackLayout
        objectName: "stackLayout"
        anchors.fill: parent
        visible: !control._useSourceMode && control.pageComponents.length === 0
        
        Component.onCompleted: {
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
        }
    }
    
    // ==================== pageComponents Mode 组件列表模式 ====================
    Item {
        id: componentContainer
        anchors.fill: parent
        visible: !control._useSourceMode && control.pageComponents.length > 0
        
        Repeater {
            id: componentRepeater
            model: (!control._useSourceMode && control.pageComponents.length > 0) ? control.pageComponents.length : 0
            
            Loader {
                id: componentLoader
                width: componentContainer.width
                height: componentContainer.height
                sourceComponent: control.pageComponents[index]
                active: !control.lazyLoading || index === control.currentIndex || control._loaders[index]?.active
                visible: index === control._displayIndex
                opacity: index === control._displayIndex ? 1 : 0
                scale: 1
                transformOrigin: Item.Center
                asynchronous: control.lazyLoading
                
                property int pageIndex: index
                
                Component.onCompleted: {
                    var loaders = control._loaders.slice()
                    loaders[index] = componentLoader
                    control._loaders = loaders
                }
                
                onLoaded: control.pageLoaded(index)
            }
        }
    }
    
    // ==================== pageSources Mode 文件路径模式 ====================
    Item {
        id: sourceContainer
        anchors.fill: parent
        visible: control._useSourceMode
        
        Repeater {
            id: sourceRepeater
            model: control._useSourceMode ? control.pageSources.length : 0
            
            Loader {
                id: sourceLoader
                width: sourceContainer.width
                height: sourceContainer.height
                // latch 用独立布尔 _loadOnce, 不自引用 active(自引用——含绕 _loaders[index]
                // 间接自引用——会因 Loader.active 默认 true / _loaders 数组 slice 重建触发
                // 连锁, 导致所有页一启动就 active 全加载, 懒加载失效)。
                // _loadOnce 初始 false → 初始 active 仅跟 index===currentIndex(只当前页);
                // 页面一旦被激活 onActiveChanged 锁 _loadOnce=true, 切走再切回仍 active,
                // source 不清空(避免 status===Ready latch 的切走退出 Ready→source 清空→永久轮询死锁)。
                property bool _loadOnce: false
                onActiveChanged: if (active) _loadOnce = true
                source: control.lazyLoading ? (index === control.currentIndex || _loadOnce ? control.pageSources[index] : "") : control.pageSources[index]
                active: !control.lazyLoading || index === control.currentIndex || _loadOnce
                visible: index === control._displayIndex
                opacity: index === control._displayIndex ? 1 : 0
                scale: 1
                transformOrigin: Item.Center
                asynchronous: control.lazyLoading
                
                property int pageIndex: index

                Component.onCompleted: {
                    var loaders = control._loaders.slice()
                    loaders[index] = sourceLoader
                    control._loaders = loaders
                }

                // latch on actual load completion 加载完成即合锁。
                // 初始当前页(主页)启动时 active 默认即 true, 绑定算出 true 但值未发生
                // 变化 → onActiveChanged 不触发 → _loadOnce 漏锁 → 切走被卸载、切回重新
                // 懒加载。onLoaded 是"已加载"的权威信号, 主页启动会触发, 在此补锁兜底。
                onLoaded: {
                    _loadOnce = true
                    control.pageLoaded(index)
                }
            }
        }
    }
    
    // ==================== QML Lazy Loading Helper (for pure QML) QML懒加载辅助（纯QML使用） ====================
    LazyLoadingHelper {
        id: lazyHelper
        anchors.fill: parent
        visible: control.lazyLoading && control._useSourceMode
        loaders: control._loaders
        targetIndex: control.currentIndex
        currentVisibleIndex: control._displayIndex
        loadingText: control.loadingText
        animationType: control.animationType
        animationDuration: control.animationDuration
        popUpOffset: control.popUpOffset
        isPageLoadedFunc: control._isPageLoaded
        activateLoaderFunc: control._activateLoader

        onLoadingComplete: (targetIdx, prevIdx) => {
            // 更新实际显示页(不写 currentIndex: 它已是 targetIdx 且不能命令式写,
            // 否则打破外部 'currentIndex: window.currentIndex' 绑定)。
            control.previousIndex = control._displayIndex
            control._displayIndex = targetIdx

            var newWidget = control.widget(targetIdx)
            if (newWidget) {
                newWidget.visible = true
                switch (control.animationType) {
                    case Enums.animation.opacity:
                        newWidget.opacity = 0
                        break
                    case Enums.animation.popup:
                        newWidget.opacity = 0
                        newWidget.y = control.popUpOffset
                        break
                    case Enums.animation.popdown:
                        newWidget.opacity = 0
                        newWidget.y = -control.popUpOffset
                        break
                    case Enums.animation.zoom:
                        newWidget.scale = 0
                        newWidget.opacity = 1
                        break
                    case Enums.animation.slide:
                    case Enums.animation.card:
                        newWidget.x = control.width
                        newWidget.opacity = 1
                        break
                    default:
                        newWidget.opacity = 0
                }
            }
            control._doEnterAnimation(targetIdx)
        }
    }
    // ==================== Index Change Handler 索引变化处理 ====================
    onCurrentIndexChanged: {
        // currentIndex 是目标页(外部输入)。用 _displayIndex(实际显示页)判重,
        // 内部绝不回写 currentIndex(否则打破外部声明式绑定)。
        if (currentIndex === _displayIndex) return
        if (currentIndex < 0 || currentIndex >= count) return

        // QML lazy loading mode: use LazyLoadingHelper
        // QML懒加载模式：使用LazyLoadingHelper
        if (lazyLoading && _useSourceMode && !_isPageLoaded(currentIndex)) {
            // 不回退 currentIndex: 旧页靠 _displayIndex(仍为旧值)保持可见,
            // loading 完成后由 LazyLoadingHelper.onLoadingComplete 更新 _displayIndex。
            lazyHelper.showLoadingAndSwitch(currentIndex)
        } else {
            // Normal switch or Python mode 正常切换或Python模式
            previousIndex = _displayIndex
            _doAnimation(_displayIndex, currentIndex)
            _displayIndex = currentIndex
        }
    }
}
