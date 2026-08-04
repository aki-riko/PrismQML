// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedZoomAnimations - Zoom transition backend 缩放切页后端
QtObject {
    id: backend

    required property Item host
    property Item _oldWidget: null
    property Item _newWidget: null
    property Item _enterWidget: null
    readonly property bool running: zoomOutAnimation.running || zoomInAnimation.running || enterAnimation.running
    readonly property SequentialAnimation zoomOutAnimation: SequentialAnimation {
        NumberAnimation {
            target: backend._oldWidget
            property: "scale"
            from: 1
            to: 0
            duration: backend.host.animationDuration / 2
            easing.type: Easing.InQuad
        }
        ScriptAction {
            script: {
                backend._oldWidget.visible = false
                backend._oldWidget.scale = 1
                backend._newWidget.visible = true
                backend._newWidget.scale = 0
                backend.zoomInAnimation.start()
            }
        }
    }
    readonly property NumberAnimation zoomInAnimation: NumberAnimation {
        target: backend._newWidget
        property: "scale"
        from: 0
        to: 1
        duration: backend.host.animationDuration / 2
        easing.type: Easing.OutQuad
        onFinished: backend.finished()
    }
    readonly property NumberAnimation enterAnimation: NumberAnimation {
        target: backend._enterWidget
        property: "scale"
        from: 0
        to: 1
        duration: backend.host.animationDuration / 2
        easing.type: Easing.OutQuad
        onFinished: backend.finished()
    }

    signal finished()

    function widget(index) { return host.widget(index) }
    function stopAllAnimations() {
        zoomOutAnimation.stop()
        zoomInAnimation.stop()
        enterAnimation.stop()
        if (_oldWidget) {
            _oldWidget.visible = false
            _oldWidget.scale = 1
        }
    }
    function transition(oldIndex, newIndex) {
        stopAllAnimations()
        _enterWidget = null
        _oldWidget = widget(oldIndex)
        _newWidget = widget(newIndex)
        if (!_oldWidget || !_newWidget) return
        _oldWidget.visible = true
        _oldWidget.opacity = 1
        _oldWidget.scale = 1
        _newWidget.visible = false
        _newWidget.opacity = 1
        _newWidget.scale = 1
        zoomOutAnimation.start()
    }
    function enterOnly(newIndex) {
        stopAllAnimations()
        _oldWidget = null
        _newWidget = null
        _enterWidget = widget(newIndex)
        if (!_enterWidget) return
        enterAnimation.start()
    }
}
