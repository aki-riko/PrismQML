// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedSlideAnimations - Slide transition backend 滑动切页后端
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
            }
            backend.finished()
        }

        NumberAnimation { id: slideOut; target: backend._oldWidget; property: "x"; from: 0; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: slideIn; target: backend._newWidget; property: "x"; to: 0; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
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
            _oldWidget.x = 0
            _oldWidget.visible = false
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
        var direction = isBack ? -1 : 1
        _newWidget.x = host.control.width * direction
        _newWidget.opacity = 1
        _newWidget.visible = true
        slideOut.to = -host.control.width * direction
        slideIn.from = host.control.width * direction
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
