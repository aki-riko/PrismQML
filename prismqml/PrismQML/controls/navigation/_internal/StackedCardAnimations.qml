// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedCardAnimations - Card transition backend 卡片层叠后端
QtObject {
    id: backend

    required property Item host
    property Item _oldWidget: null
    property Item _newWidget: null
    property bool _enterOnly: false
    readonly property bool running: transitionGroup.running || enterAnimation.running
    readonly property ParallelAnimation transitionGroup: ParallelAnimation {
        onFinished: {
            if (backend._oldWidget) {
                backend._oldWidget.visible = false
                backend._oldWidget.x = 0
                backend._oldWidget.scale = 1
                backend._oldWidget.opacity = 1
            }
            backend.finished()
        }

        NumberAnimation { id: slideAnimation; property: "x"; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: scaleAnimation; property: "scale"; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: opacityAnimation; property: "opacity"; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
    }
    readonly property NumberAnimation enterAnimation: NumberAnimation {
        target: backend._newWidget
        property: "x"
        to: 0
        duration: backend.host.animationDuration
        easing.type: Easing.OutCubic
        onFinished: backend.finished()
    }

    signal finished()

    function widget(index) { return host.widget(index) }
    function stopAllAnimations() {
        transitionGroup.stop()
        enterAnimation.stop()
        if (_oldWidget) {
            _oldWidget.visible = false
            _oldWidget.x = 0
            _oldWidget.scale = 1
            _oldWidget.opacity = 1
        }
        if (_enterOnly && _newWidget) _newWidget.x = 0
    }
    function transition(oldIndex, newIndex, isBack) {
        stopAllAnimations()
        _enterOnly = false
        _oldWidget = widget(oldIndex)
        _newWidget = widget(newIndex)
        if (!_oldWidget || !_newWidget) return
        _oldWidget.visible = true
        _oldWidget.opacity = 1
        _oldWidget.x = 0
        _oldWidget.scale = 1
        if (isBack) {
            _newWidget.visible = true
            _newWidget.x = 0
            _newWidget.scale = host.cardScale
            _newWidget.opacity = host.cardOpacity
            slideAnimation.target = _oldWidget
            slideAnimation.from = 0
            slideAnimation.to = host.control.width
            scaleAnimation.target = _newWidget
            scaleAnimation.from = host.cardScale
            scaleAnimation.to = 1
            opacityAnimation.target = _newWidget
            opacityAnimation.from = host.cardOpacity
            opacityAnimation.to = 1
        } else {
            _newWidget.visible = true
            _newWidget.x = host.control.width
            _newWidget.scale = 1
            _newWidget.opacity = 1
            slideAnimation.target = _newWidget
            slideAnimation.from = host.control.width
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
    function enterOnly(newIndex) {
        stopAllAnimations()
        _enterOnly = true
        _oldWidget = null
        _newWidget = widget(newIndex)
        if (!_newWidget) return
        enterAnimation.start()
    }
}
