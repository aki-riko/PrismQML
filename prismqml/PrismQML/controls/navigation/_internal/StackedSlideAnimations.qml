// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "." as NavigationInternal

// StackedSlideAnimations - Slide transition backend 滑动切页后端
QtObject {
    id: backend

    required property Item host
    property Item _oldWidget: null
    property Item _newWidget: null
    property bool _enterOnly: false
    property bool _vertical: false
    readonly property string _positionProperty: _vertical ? "y" : "x"
    readonly property QtObject zOrderGuard: NavigationInternal.StackedZOrderGuard {}
    readonly property bool running: transitionGroup.running || enterAnimation.running

    readonly property ParallelAnimation transitionGroup: ParallelAnimation {
        onFinished: {
            if (backend._oldWidget) {
                backend._oldWidget.visible = false
                backend._resetPosition(backend._oldWidget)
            }
            backend.zOrderGuard.restore()
            backend.finished()
        }

        NumberAnimation { id: slideOut; target: backend._oldWidget; property: backend._positionProperty; from: 0; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: slideIn; target: backend._newWidget; property: backend._positionProperty; to: 0; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
    }
    readonly property NumberAnimation enterAnimation: NumberAnimation {
        target: backend._newWidget
        property: backend._positionProperty
        to: 0
        duration: backend.host.animationDuration
        easing.type: Easing.OutCubic
        onFinished: backend.finished()
    }

    signal finished()

    function widget(index) { return host.widget(index) }
    function _resetPosition(widget) {
        if (!widget) return
        widget.x = 0
        widget.y = 0
    }
    function _setPosition(widget, value) {
        if (!widget) return
        if (_vertical) widget.y = value
        else widget.x = value
    }
    function _axisLength() {
        return _vertical ? host.control.height : host.control.width
    }

    function stopAllAnimations() {
        transitionGroup.stop()
        enterAnimation.stop()
        zOrderGuard.restore()
        if (_oldWidget) {
            _resetPosition(_oldWidget)
            _oldWidget.visible = false
        }
        if (_enterOnly && _newWidget) _resetPosition(_newWidget)
    }
    function transition(oldIndex, newIndex, isBack, vertical) {
        stopAllAnimations()
        _vertical = Boolean(vertical)
        _enterOnly = false
        _oldWidget = widget(oldIndex)
        _newWidget = widget(newIndex)
        if (!_oldWidget || !_newWidget) return
        zOrderGuard.capture(_oldWidget, _newWidget)
        _oldWidget.visible = true
        _oldWidget.opacity = 1
        _resetPosition(_oldWidget)
        var direction = isBack ? -1 : 1
        var distance = _axisLength() * direction
        _setPosition(_newWidget, distance)
        _newWidget.opacity = 1
        _newWidget.visible = true
        slideOut.to = -distance
        slideIn.from = distance
        transitionGroup.start()
    }
    function enterOnly(newIndex, vertical) {
        stopAllAnimations()
        _vertical = Boolean(vertical)
        _enterOnly = true
        _oldWidget = null
        _newWidget = widget(newIndex)
        if (!_newWidget) return
        _setPosition(_newWidget, _axisLength())
        enterAnimation.start()
    }
}
