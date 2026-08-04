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
        var backend = _ensureBackend(_sourceForType(Enums.animation.slide))
        if (backend) backend.transition(oldIndex, newIndex, isBack)
    }
    function enterSlideOnly(newIndex) {
        var backend = _ensureBackend(
                    _sourceForType(control.animationType === Enums.animation.card ?
                                       Enums.animation.card : Enums.animation.slide))
        if (backend) backend.enterOnly(newIndex)
    }
    function popUpTransition(oldIndex, newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.popup))
        if (backend) backend.transition(oldIndex, newIndex)
    }
    function enterPopUpOnly(newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.popup))
        if (backend) backend.enterOnly(newIndex)
    }
    function popDownTransition(oldIndex, newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.popdown))
        if (backend) backend.transition(oldIndex, newIndex)
    }
    function enterPopDownOnly(newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.popdown))
        if (backend) backend.enterOnly(newIndex)
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
        var backend = _ensureBackend(_sourceForType(Enums.animation.card))
        if (backend) backend.transition(oldIndex, newIndex, isBack)
    }

    // ==================== Internal Methods 内部方法 ====================
    function _sourceForType(type) {
        switch (type) {
            case Enums.animation.opacity:
                return Qt.resolvedUrl("StackedFadeAnimations.qml")
            case Enums.animation.popup:
                return Qt.resolvedUrl("StackedPopUpAnimations.qml")
            case Enums.animation.popdown:
                return Qt.resolvedUrl("StackedPopDownAnimations.qml")
            case Enums.animation.slide:
                return Qt.resolvedUrl("StackedSlideAnimations.qml")
            case Enums.animation.card:
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
