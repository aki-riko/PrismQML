// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// StackedModeAnimations - Mode-scoped stacked animations 按模式创建的堆叠动画
Item {
    id: animations

    // ==================== Required Props 必需属性 ====================
    required property Item control
    required property int animationDuration
    required property real cardScale
    required property real cardOpacity

    // ==================== Internal Props 内部属性 ====================
    property bool _completed: false
    readonly property url _desiredSource: _sourceForType(control.animationType)
    readonly property bool running: backendLoader.item
        ? Boolean(backendLoader.item.running) : false

    // ==================== Signals 信号 ====================
    signal animationFinished(int currentIndex)

    // ==================== Public Methods 公开方法 ====================
    function widget(index) { return control.widget(index) }

    function prepareEnter(index) {
        var newWidget = widget(index)
        if (!newWidget) return false

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
            case Enums.animation.slide_vertical:
            case Enums.animation.card_vertical:
                newWidget.x = 0
                newWidget.y = control.height
                newWidget.opacity = 1
                break
            case Enums.animation.slide_horizontal:
            case Enums.animation.card_horizontal:
            case Enums.animation.slide_fade:
                newWidget.x = control.width
                newWidget.opacity = 1
                break
            default:
                newWidget.opacity = 0
        }
        return true
    }

    function stopAllAnimations() {
        if (backendLoader.item) backendLoader.item.stopAllAnimations()
    }

    function fadeTransition(oldIndex, newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.opacity))
        if (backend) backend.transition(oldIndex, newIndex)
    }
    function enterFadeOnly(newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.opacity))
        if (backend) backend.enterOnly(newIndex)
    }
    function slideTransition(oldIndex, newIndex, isBack) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.slide_horizontal))
        if (backend) backend.transition(oldIndex, newIndex, isBack, _isVerticalAxis())
    }
    function slideFadeTransition(oldIndex, newIndex, isBack) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.slide_fade))
        if (backend) backend.transition(oldIndex, newIndex, isBack)
    }
    function enterSlideOnly(newIndex) {
        var isCardAxis = control.animationType === Enums.animation.card_horizontal
                || control.animationType === Enums.animation.card_vertical
        var backend = _ensureBackend(_sourceForType(isCardAxis ?
                    Enums.animation.card_horizontal : Enums.animation.slide_horizontal))
        if (backend) backend.enterOnly(newIndex, _isVerticalAxis())
    }
    function enterSlideFadeOnly(newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.slide_fade))
        if (backend) backend.enterOnly(newIndex)
    }
    function popUpTransition(oldIndex, newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.popup))
        if (backend) {
            backend.configure(false)
            backend.transition(oldIndex, newIndex)
        }
    }
    function enterPopUpOnly(newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.popup))
        if (backend) {
            backend.configure(false)
            backend.enterOnly(newIndex)
        }
    }
    function popDownTransition(oldIndex, newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.popdown))
        if (backend) {
            backend.configure(true)
            backend.transition(oldIndex, newIndex)
        }
    }
    function enterPopDownOnly(newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.popdown))
        if (backend) {
            backend.configure(true)
            backend.enterOnly(newIndex)
        }
    }
    function zoomTransition(oldIndex, newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.zoom))
        if (backend) backend.transition(oldIndex, newIndex)
    }
    function enterZoomOnly(newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.zoom))
        if (backend) backend.enterOnly(newIndex)
    }
    function cardTransition(oldIndex, newIndex, isBack) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.card_horizontal))
        if (backend) backend.transition(oldIndex, newIndex, isBack, _isVerticalAxis())
    }

    // ==================== Internal Methods 内部方法 ====================
    // Axis of the currently configured mode: slide and card both exist in a
    // horizontal and a vertical variant.
    // 当前模式的轴向：slide 与 card 都只有水平、垂直两个变体。
    function _isVerticalAxis() {
        return control.animationType === Enums.animation.slide_vertical
                || control.animationType === Enums.animation.card_vertical
    }

    function _sourceForType(type) {
        switch (type) {
            case Enums.animation.opacity:
                return Qt.resolvedUrl("StackedFadeAnimations.qml")
            case Enums.animation.popup:
                return Qt.resolvedUrl("StackedPopAnimations.qml")
            case Enums.animation.popdown:
                return Qt.resolvedUrl("StackedPopAnimations.qml")
            case Enums.animation.slide_horizontal:
            case Enums.animation.slide_vertical:
                return Qt.resolvedUrl("StackedSlideAnimations.qml")
            case Enums.animation.slide_fade:
                return Qt.resolvedUrl("StackedSlideFadeAnimations.qml")
            case Enums.animation.card_horizontal:
            case Enums.animation.card_vertical:
                return Qt.resolvedUrl("StackedCardAnimations.qml")
            case Enums.animation.zoom:
                return Qt.resolvedUrl("StackedZoomAnimations.qml")
            case Enums.animation.none: return ""
            default: return Qt.resolvedUrl("StackedFadeAnimations.qml")
        }
    }

    function _ensureBackend(source) {
        var requested = source ? source.toString() : ""
        var loaded = backendLoader.source ? backendLoader.source.toString() : ""
        if (requested === loaded && backendLoader.item) return backendLoader.item

        if (backendLoader.item) backendLoader.item.stopAllAnimations()
        if (requested === "") {
            backendLoader.source = ""
            return null
        }
        backendLoader.setSource(source, {"host": animations})
        return backendLoader.item
    }

    function _preloadDesiredBackend() {
        if (backendLoader.item && backendLoader.item.running) return
        _ensureBackend(_desiredSource)
    }

    function _handleBackendFinished() {
        animations.animationFinished(control.currentIndex)
        if (backendLoader.source.toString() !== _desiredSource.toString()) {
            Qt.callLater(animations._preloadDesiredBackend)
        }
    }

    on_DesiredSourceChanged: {
        if (_completed) _preloadDesiredBackend()
    }
    Component.onCompleted: {
        _completed = true
        _preloadDesiredBackend()
    }

    // ==================== Content 内容 ====================
    Loader {
        id: backendLoader

        visible: false
        asynchronous: false
        onLoaded: item.finished.connect(animations._handleBackendFinished)
    }
}
