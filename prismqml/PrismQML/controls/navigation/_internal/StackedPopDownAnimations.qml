// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedPopDownAnimations - Downward popup backend 下落切页后端
QtObject {
    id: backend

    required property Item host
    property Item _oldWidget: null
    property Item _newWidget: null
    readonly property bool running: animationGroup.running
    readonly property ParallelAnimation animationGroup: ParallelAnimation {
        onStarted: { if (backend._oldWidget) backend._oldWidget.visible = false }
        onFinished: backend.finished()

        NumberAnimation { id: yAnimation; target: backend._newWidget; property: "y"; to: 0; duration: backend.host.animationDuration; easing.type: Easing.OutBounce }
        NumberAnimation { target: backend._newWidget; property: "opacity"; from: 0.0; to: 1.0; duration: backend.host.animationDuration; easing.type: Easing.OutQuad }
    }

    signal finished()

    function widget(index) { return host.widget(index) }
    function stopAllAnimations() {
        animationGroup.stop()
        if (_oldWidget) {
            _oldWidget.visible = false
            _oldWidget.y = 0
        } else if (_newWidget) {
            _newWidget.y = 0
        }
    }
    function transition(oldIndex, newIndex) {
        stopAllAnimations()
        _oldWidget = widget(oldIndex)
        _newWidget = widget(newIndex)
        if (!_oldWidget || !_newWidget) return
        _oldWidget.visible = true
        _oldWidget.opacity = 1
        _oldWidget.y = 0
        var offset = -host.control.popUpOffset
        _newWidget.y = offset
        _newWidget.opacity = 0
        _newWidget.visible = true
        yAnimation.from = offset
        animationGroup.start()
    }
    function enterOnly(newIndex) {
        stopAllAnimations()
        _oldWidget = null
        _newWidget = widget(newIndex)
        if (!_newWidget) return
        yAnimation.from = _newWidget.y
        animationGroup.start()
    }
}
