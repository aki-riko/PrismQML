// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "." as NavigationInternal

// StackedSlideFadeAnimations - Slide and fade transition backend 滑动淡入淡出切页后端
// Runs on the axis given by the caller: the incoming page slides in from that
// edge while both pages cross-fade.
// 在调用方给定的轴上运行：新页从对应边滑入，同时新旧页交叉淡入淡出。
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
                backend._oldWidget.opacity = 1
            }
            backend.zOrderGuard.restore()
            backend.finished()
        }

        NumberAnimation { id: oldSlide; property: backend._positionProperty; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: oldOpacity; property: "opacity"; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: newSlide; property: backend._positionProperty; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: newOpacity; property: "opacity"; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
    }

    readonly property ParallelAnimation enterAnimation: ParallelAnimation {
        onFinished: backend.finished()

        NumberAnimation { target: backend._newWidget; property: backend._positionProperty; to: 0; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { target: backend._newWidget; property: "opacity"; to: 1; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
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
            _oldWidget.visible = false
            _resetPosition(_oldWidget)
            _oldWidget.opacity = 1
        }
        if (_enterOnly && _newWidget) {
            _resetPosition(_newWidget)
            _newWidget.opacity = 1
        }
    }

    function transition(oldIndex, newIndex, isBack, vertical) {
        stopAllAnimations()
        _vertical = Boolean(vertical)
        _enterOnly = false
        _oldWidget = widget(oldIndex)
        _newWidget = widget(newIndex)
        if (!_oldWidget || !_newWidget) return

        zOrderGuard.capture(_oldWidget, _newWidget)

        var direction = isBack ? -1 : 1
        var distance = _axisLength()
        _oldWidget.visible = true
        _resetPosition(_oldWidget)
        _oldWidget.opacity = 1
        _newWidget.visible = true
        _resetPosition(_newWidget)
        _setPosition(_newWidget, distance * direction)
        _newWidget.opacity = 0

        oldSlide.target = _oldWidget
        oldSlide.from = 0
        oldSlide.to = -distance * 0.2 * direction
        oldOpacity.target = _oldWidget
        oldOpacity.from = 1
        oldOpacity.to = 0.5
        newSlide.target = _newWidget
        newSlide.from = distance * direction
        newSlide.to = 0
        newOpacity.target = _newWidget
        newOpacity.from = 0
        newOpacity.to = 1
        transitionGroup.start()
    }

    function enterOnly(newIndex, vertical) {
        stopAllAnimations()
        _vertical = Boolean(vertical)
        _enterOnly = true
        _oldWidget = null
        _newWidget = widget(newIndex)
        if (!_newWidget) return
        _newWidget.visible = true
        _resetPosition(_newWidget)
        _setPosition(_newWidget, _axisLength())
        _newWidget.opacity = 0
        enterAnimation.start()
    }
}
