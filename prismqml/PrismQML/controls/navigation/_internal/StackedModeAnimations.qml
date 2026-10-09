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
            case Enums.animation.pop:
            case Enums.animation.bounce:
                newWidget.x = 0
                newWidget.y = 0
                _setEntryPosition(newWidget, _popVerticalAxis(), _popEntrySign(false))
                newWidget.opacity = 0
                break
            case Enums.animation.zoom:
                newWidget.scale = 0
                newWidget.opacity = 1
                break
            case Enums.animation.slide:
            case Enums.animation.card:
                newWidget.x = 0
                newWidget.y = 0
                if (_isVerticalAxis()) newWidget.y = control.height
                else newWidget.x = control.width
                newWidget.opacity = 1
                break
            case Enums.animation.slide_fade:
                newWidget.x = 0
                newWidget.y = 0
                if (_isVerticalAxis()) newWidget.y = control.height
                else newWidget.x = control.width
                newWidget.opacity = 0
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
        if (backend) backend.transition(oldIndex, newIndex, isBack, _isVerticalAxis())
    }
    function slideFadeTransition(oldIndex, newIndex, isBack) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.slide_fade))
        if (backend) backend.transition(oldIndex, newIndex, isBack, _isVerticalAxis())
    }
    function enterSlideOnly(newIndex) {
        var backend = _ensureBackend(_sourceForType(
                    control.animationType === Enums.animation.card
                    ? Enums.animation.card : Enums.animation.slide))
        if (backend) backend.enterOnly(newIndex, _isVerticalAxis())
    }
    function enterSlideFadeOnly(newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.slide_fade))
        if (backend) backend.enterOnly(newIndex, _isVerticalAxis())
    }
    function popTransition(oldIndex, newIndex, isBack) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.pop))
        if (backend) backend.transition(
                    oldIndex, newIndex,
                    _popVerticalAxis(), _popEntrySign(isBack), _isBounceMode())
    }
    function enterPopOnly(newIndex) {
        var backend = _ensureBackend(_sourceForType(Enums.animation.pop))
        if (backend) backend.enterOnly(
                    newIndex, _popVerticalAxis(), _popEntrySign(false), _isBounceMode())
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
        if (backend) backend.transition(oldIndex, newIndex, isBack, _isVerticalAxis())
    }

    // ==================== Internal Methods 内部方法 ====================
    // Axis of slide / slide_fade / card; pop / bounce follow it only while origin is auto.
    // slide / slide_fade / card 的轴向；pop / bounce 仅在 origin 为 auto 时跟随它。
    function _isVerticalAxis() {
        return control.animationOrientation === Qt.Vertical
    }

    // Landing curve of the shared pop backend: pop is smooth, bounce is elastic.
    // 共享 pop 后端的落位曲线：pop 平滑，bounce 回弹。
    function _isBounceMode() {
        return control.animationType === Enums.animation.bounce
    }

    // Entry edge of pop / bounce: a pinned origin wins; origin_auto keeps the axis
    // from animationOrientation and takes the edge from the switch direction.
    // pop / bounce 进入边：钉住的 origin 优先；origin_auto 时轴取 animationOrientation，
    // 边取切换方向。
    function _popVerticalAxis() {
        switch (control.animationOrigin) {
            case Enums.animation.origin_top:
            case Enums.animation.origin_bottom:
                return true
            case Enums.animation.origin_left:
            case Enums.animation.origin_right:
                return false
            default:
                return _isVerticalAxis()
        }
    }

    function _popEntrySign(isBack) {
        switch (control.animationOrigin) {
            case Enums.animation.origin_top:
            case Enums.animation.origin_left:
                return -1
            case Enums.animation.origin_bottom:
            case Enums.animation.origin_right:
                return 1
            default:
                return isBack ? -1 : 1
        }
    }

    function _setEntryPosition(widget, vertical, entrySign) {
        var offset = entrySign >= 0 ? control.popUpOffset : -control.popUpOffset
        if (vertical) widget.y = offset
        else widget.x = offset
    }

    function _sourceForType(type) {
        switch (type) {
            case Enums.animation.opacity:
                return Qt.resolvedUrl("StackedFadeAnimations.qml")
            case Enums.animation.pop:
            case Enums.animation.bounce:
                return Qt.resolvedUrl("StackedPopAnimations.qml")
            case Enums.animation.slide:
                return Qt.resolvedUrl("StackedSlideAnimations.qml")
            case Enums.animation.slide_fade:
                return Qt.resolvedUrl("StackedSlideFadeAnimations.qml")
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
