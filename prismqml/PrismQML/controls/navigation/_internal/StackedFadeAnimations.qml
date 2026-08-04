// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedFadeAnimations - Fade transition backend 淡入淡出后端
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
                backend._oldWidget.opacity = 1.0
            }
            backend.finished()
        }

        NumberAnimation { target: backend._oldWidget; property: "opacity"; from: 1.0; to: 0.0; duration: backend.host.animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { target: backend._newWidget; property: "opacity"; from: 0.0; to: 1.0; duration: backend.host.animationDuration; easing.type: Easing.InCubic }
    }
    readonly property NumberAnimation enterAnimation: NumberAnimation {
        target: backend._newWidget
        property: "opacity"
        from: 0.0
        to: 1.0
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
            _oldWidget.opacity = 1
            _oldWidget.visible = false
        }
        if (!_enterOnly && _newWidget) {
            _newWidget.y = 0
            _newWidget.x = 0
            _newWidget.scale = 1
        }
    }
    function transition(oldIndex, newIndex) {
        stopAllAnimations()
        _enterOnly = false
        _oldWidget = widget(oldIndex)
        _newWidget = widget(newIndex)
        if (!_oldWidget || !_newWidget) return
        _oldWidget.visible = true
        _oldWidget.opacity = 1
        _newWidget.opacity = 0
        _newWidget.visible = true
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
