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
    readonly property url _fadeSource: Qt.resolvedUrl("StackedFadeAnimations.qml")
    readonly property url _slideSource: Qt.resolvedUrl("StackedSlideAnimations.qml")
    readonly property url _popUpSource: Qt.resolvedUrl("StackedPopUpAnimations.qml")
    readonly property url _popDownSource: Qt.resolvedUrl("StackedPopDownAnimations.qml")
    readonly property url _zoomSource: Qt.resolvedUrl("StackedZoomAnimations.qml")
    readonly property url _cardSource: Qt.resolvedUrl("StackedCardAnimations.qml")
    readonly property url _desiredSource: _sourceForType(control.animationType)
    readonly property QtObject _backend: backendLoader.item

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
            case Enums.animation.slide:
            case Enums.animation.card:
                newWidget.x = control.width
                newWidget.opacity = 1
                break
            default:
                newWidget.opacity = 0
        }
        return true
    }

    function stopAllAnimations() {
        if (_backend) _backend.stopAllAnimations()
    }

    function fadeTransition(oldIndex, newIndex) {
        var backend = _ensureBackend(_fadeSource)
        if (backend) backend.transition(oldIndex, newIndex)
    }
    function enterFadeOnly(newIndex) {
        var backend = _ensureBackend(_fadeSource)
        if (backend) backend.enterOnly(newIndex)
    }
    function slideTransition(oldIndex, newIndex, isBack) {
        var backend = _ensureBackend(_slideSource)
        if (backend) backend.transition(oldIndex, newIndex, isBack)
    }
    function enterSlideOnly(newIndex) {
        var backend = _ensureBackend(
                    control.animationType === Enums.animation.card ? _cardSource : _slideSource)
        if (backend) backend.enterOnly(newIndex)
    }
    function popUpTransition(oldIndex, newIndex) {
        var backend = _ensureBackend(_popUpSource)
        if (backend) backend.transition(oldIndex, newIndex)
    }
    function enterPopUpOnly(newIndex) {
        var backend = _ensureBackend(_popUpSource)
        if (backend) backend.enterOnly(newIndex)
    }
    function popDownTransition(oldIndex, newIndex) {
        var backend = _ensureBackend(_popDownSource)
        if (backend) backend.transition(oldIndex, newIndex)
    }
    function enterPopDownOnly(newIndex) {
        var backend = _ensureBackend(_popDownSource)
        if (backend) backend.enterOnly(newIndex)
    }
    function zoomTransition(oldIndex, newIndex) {
        var backend = _ensureBackend(_zoomSource)
        if (backend) backend.transition(oldIndex, newIndex)
    }
    function enterZoomOnly(newIndex) {
        var backend = _ensureBackend(_zoomSource)
        if (backend) backend.enterOnly(newIndex)
    }
    function cardTransition(oldIndex, newIndex, isBack) {
        var backend = _ensureBackend(_cardSource)
        if (backend) backend.transition(oldIndex, newIndex, isBack)
    }

    // ==================== Internal Methods 内部方法 ====================
    function _sourceForType(type) {
        switch (type) {
            case Enums.animation.opacity: return _fadeSource
            case Enums.animation.popup: return _popUpSource
            case Enums.animation.popdown: return _popDownSource
            case Enums.animation.slide: return _slideSource
            case Enums.animation.card: return _cardSource
            case Enums.animation.zoom: return _zoomSource
            case Enums.animation.none: return ""
            default: return _fadeSource
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
        if (_backend && _backend.running) return
        _ensureBackend(_desiredSource)
    }

    function _handleBackendFinished() {
        animations.animationFinished(control.currentIndex)
        if (backendLoader.source.toString() !== _desiredSource.toString()) {
            Qt.callLater(animations._preloadDesiredBackend)
        }
    }

    Component.onCompleted: _preloadDesiredBackend()

    // ==================== Content 内容 ====================
    Connections {
        function onAnimationTypeChanged() { animations._preloadDesiredBackend() }

        target: animations.control
    }

    Loader {
        id: backendLoader

        visible: false
        asynchronous: false
        onLoaded: item.finished.connect(animations._handleBackendFinished)
    }
}
