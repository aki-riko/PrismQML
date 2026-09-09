// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "." as NavigationInternal

// StackedSlideFadeAnimations - Slide and fade transition backend 滑动淡入淡出切页后端
QtObject {
    id: backend

    required property Item host
    property Item _oldWidget: null
    property Item _newWidget: null
    property bool _enterOnly: false
    readonly property QtObject zOrderGuard: NavigationInternal.StackedZOrderGuard {}
    readonly property bool running: transitionGroup.running || enterAnimation.running

    readonly property ParallelAnimation transitionGroup: ParallelAnimation {
        onFinished: {
            if (backend._oldWidget) {
                backend._oldWidget.visible = false
                backend._oldWidget.x = 0
                backend._oldWidget.opacity = 1
            }
            backend.zOrderGuard.restore()
            backend.finished()
        }

        NumberAnimation { id: oldX; property: "x"; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: oldOpacity; property: "opacity"; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: newX; property: "x"; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: newOpacity; property: "opacity"; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
    }

    readonly property ParallelAnimation enterAnimation: ParallelAnimation {
        onFinished: backend.finished()

        NumberAnimation { target: backend._newWidget; property: "x"; to: 0; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { target: backend._newWidget; property: "opacity"; to: 1; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
    }

    signal finished()

    function widget(index) { return host.widget(index) }

    function stopAllAnimations() {
        transitionGroup.stop()
        enterAnimation.stop()
        zOrderGuard.restore()
        if (_oldWidget) {
            _oldWidget.visible = false
            _oldWidget.x = 0
            _oldWidget.opacity = 1
        }
        if (_enterOnly && _newWidget) {
            _newWidget.x = 0
            _newWidget.opacity = 1
        }
    }

    function transition(oldIndex, newIndex, isBack) {
        stopAllAnimations()
        _enterOnly = false
        _oldWidget = widget(oldIndex)
        _newWidget = widget(newIndex)
        if (!_oldWidget || !_newWidget) return

        zOrderGuard.capture(_oldWidget, _newWidget)

        var direction = isBack ? -1 : 1
        _oldWidget.visible = true
        _oldWidget.x = 0
        _oldWidget.opacity = 1
        _newWidget.visible = true
        _newWidget.x = host.control.width * direction
        _newWidget.opacity = 0

        oldX.target = _oldWidget
        oldX.from = 0
        oldX.to = -host.control.width * 0.2 * direction
        oldOpacity.target = _oldWidget
        oldOpacity.from = 1
        oldOpacity.to = 0.5
        newX.target = _newWidget
        newX.from = host.control.width * direction
        newX.to = 0
        newOpacity.target = _newWidget
        newOpacity.from = 0
        newOpacity.to = 1
        transitionGroup.start()
    }

    function enterOnly(newIndex) {
        stopAllAnimations()
        _enterOnly = true
        _oldWidget = null
        _newWidget = widget(newIndex)
        if (!_newWidget) return
        _newWidget.visible = true
        _newWidget.x = host.control.width
        _newWidget.opacity = 0
        enterAnimation.start()
    }
}
