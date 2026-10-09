// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedPopAnimations - Parameterized pop / bounce backend 参数化弹入切页后端
// The incoming page enters from the requested edge while fading in; the outgoing
// page is hidden immediately. The landing curve follows the mode: pop lands
// smoothly (OutQuad), bounce lands elastically (OutBounce).
// 新页从指定边进入并淡入，旧页立即隐藏；落位曲线跟随模式：pop 平滑(OutQuad)，
// bounce 回弹(OutBounce)。
QtObject {
    id: backend

    required property Item host
    property Item _oldWidget: null
    property Item _newWidget: null
    property bool _vertical: false
    property bool _bounce: true
    readonly property string _positionProperty: _vertical ? "y" : "x"
    readonly property bool running: animationGroup.running
    readonly property ParallelAnimation animationGroup: ParallelAnimation {
        onStarted: { if (backend._oldWidget) backend._oldWidget.visible = false }
        onFinished: backend.finished()

        NumberAnimation {
            id: popAnimation
            target: backend._newWidget
            property: backend._positionProperty
            to: 0
            duration: backend.host.animationDuration
            easing.type: backend._bounce ? Easing.OutBounce : Easing.OutQuad
        }
        NumberAnimation {
            target: backend._newWidget
            property: "opacity"
            from: 0.0
            to: 1.0
            duration: backend.host.animationDuration
            easing.type: Easing.OutQuad
        }
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
    function _entryOffset(entrySign) {
        return entrySign >= 0 ? host.control.popUpOffset : -host.control.popUpOffset
    }
    function stopAllAnimations() {
        animationGroup.stop()
        if (_oldWidget) {
            _oldWidget.visible = false
            _resetPosition(_oldWidget)
        } else if (_newWidget) {
            _resetPosition(_newWidget)
        }
    }
    function transition(oldIndex, newIndex, vertical, entrySign, bounce) {
        stopAllAnimations()
        _vertical = Boolean(vertical)
        _bounce = Boolean(bounce)
        _oldWidget = widget(oldIndex)
        _newWidget = widget(newIndex)
        if (!_oldWidget || !_newWidget) return
        _oldWidget.visible = true
        _oldWidget.opacity = 1
        _resetPosition(_oldWidget)
        var offset = _entryOffset(entrySign)
        _newWidget.visible = true
        _resetPosition(_newWidget)
        _setPosition(_newWidget, offset)
        _newWidget.opacity = 0
        popAnimation.from = offset
        animationGroup.start()
    }
    function enterOnly(newIndex, vertical, entrySign, bounce) {
        stopAllAnimations()
        _vertical = Boolean(vertical)
        _bounce = Boolean(bounce)
        _oldWidget = null
        _newWidget = widget(newIndex)
        if (!_newWidget) return
        var offset = _entryOffset(entrySign)
        _newWidget.visible = true
        _resetPosition(_newWidget)
        _setPosition(_newWidget, offset)
        _newWidget.opacity = 0
        popAnimation.from = offset
        animationGroup.start()
    }
}
