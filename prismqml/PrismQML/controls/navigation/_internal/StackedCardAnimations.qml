// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedCardAnimations - Card transition backend 卡片层叠后端
// Card modes slide the pages along one axis while the outgoing page scales down
// and fades; the axis is chosen by card_horizontal / card_vertical.
// 卡片模式沿单一轴向滑动页面，同时旧页缩小并淡出；轴向由 card_horizontal / card_vertical 决定。
QtObject {
    id: backend

    required property Item host
    property Item _oldWidget: null
    property Item _newWidget: null
    property bool _enterOnly: false
    property bool _vertical: false
    readonly property string _positionProperty: _vertical ? "y" : "x"
    readonly property bool running: transitionGroup.running || enterAnimation.running
    readonly property ParallelAnimation transitionGroup: ParallelAnimation {
        onFinished: {
            if (backend._oldWidget) {
                backend._oldWidget.visible = false
                backend._resetPosition(backend._oldWidget)
                backend._oldWidget.scale = 1
                backend._oldWidget.opacity = 1
            }
            backend.finished()
        }

        NumberAnimation { id: slideAnimation; property: backend._positionProperty; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: scaleAnimation; property: "scale"; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: opacityAnimation; property: "opacity"; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
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
        if (_oldWidget) {
            _oldWidget.visible = false
            _resetPosition(_oldWidget)
            _oldWidget.scale = 1
            _oldWidget.opacity = 1
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
        _oldWidget.visible = true
        _oldWidget.opacity = 1
        _oldWidget.scale = 1
        _resetPosition(_oldWidget)
        var distance = _axisLength()
        if (isBack) {
            _newWidget.visible = true
            _resetPosition(_newWidget)
            _newWidget.scale = host.cardScale
            _newWidget.opacity = host.cardOpacity
            slideAnimation.target = _oldWidget
            slideAnimation.from = 0
            slideAnimation.to = distance
            scaleAnimation.target = _newWidget
            scaleAnimation.from = host.cardScale
            scaleAnimation.to = 1
            opacityAnimation.target = _newWidget
            opacityAnimation.from = host.cardOpacity
            opacityAnimation.to = 1
        } else {
            _newWidget.visible = true
            _resetPosition(_newWidget)
            _setPosition(_newWidget, distance)
            _newWidget.scale = 1
            _newWidget.opacity = 1
            slideAnimation.target = _newWidget
            slideAnimation.from = distance
            slideAnimation.to = 0
            scaleAnimation.target = _oldWidget
            scaleAnimation.from = 1
            scaleAnimation.to = host.cardScale
            opacityAnimation.target = _oldWidget
            opacityAnimation.from = 1
            opacityAnimation.to = host.cardOpacity
        }
        transitionGroup.start()
    }
    function enterOnly(newIndex, vertical) {
        stopAllAnimations()
        _vertical = Boolean(vertical)
        _enterOnly = true
        _oldWidget = null
        _newWidget = widget(newIndex)
        if (!_newWidget) return
        _resetPosition(_newWidget)
        _setPosition(_newWidget, _axisLength())
        enterAnimation.start()
    }
}
