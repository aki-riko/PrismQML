// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// WidgetToolTipSupport - Lazy hover and tooltip prewarm support Widget 懒加载悬浮与工具提示预热支持
MouseArea {
    id: support

    // ==================== Public Props 公开属性 ====================
    property var widget: null

    // ==================== Internal Props 内部属性 ====================
    property bool _showScheduled: false
    property double _showRequestedAt: 0

    // ==================== Public Methods 公开方法 ====================
    function _prewarm() {
        if (!widget || widget.toolTipText === "") return
        if (_popupLoader.item || _popupLoader.status === Loader.Loading) return
        _popupLoader.setSource(Qt.resolvedUrl("WidgetToolTipPopup.qml"), {"widget": widget})
        _popupLoader.active = true
    }

    function showToolTip() {
        if (!widget || widget.toolTipText === "") return
        widget._toolTipShowPending = true
        _prewarm()
        if (_popupLoader.item) _popupLoader.item.show()
    }

    function hideToolTip() {
        if (!widget) return
        widget._toolTipShowPending = false
        if (_popupLoader.item) _popupLoader.item.hide()
    }

    // ==================== Internal Methods 内部方法 ====================
    function cancelTimers() {
        _showScheduled = false
        _showRequestedAt = 0
        if (_popupLoader.item) _popupLoader.item.cancelTimers()
    }

    function startShowTimer() {
        _showScheduled = true
        if (_popupLoader.item) {
            _showRequestedAt = 0
            _popupLoader.item.startShowTimer(0)
            return
        }
        _showRequestedAt = Date.now()
        _prewarm()
    }

    function stopShowTimer() {
        _showScheduled = false
        _showRequestedAt = 0
        if (_popupLoader.item) _popupLoader.item.stopShowTimer()
    }

    function startHideTimer() {
        if (_popupLoader.item) _popupLoader.item.startHideTimer()
    }

    function dismissToolTip() {
        if (!widget) return
        widget._toolTipShowPending = false
        _showScheduled = false
        if (_popupLoader.item) _popupLoader.item.dismiss()
    }

    anchors.fill: parent
    objectName: "_hoverArea"
    hoverEnabled: true
    acceptedButtons: Qt.NoButton
    propagateComposedEvents: true

    // Keep hover detection on the lightweight support object 悬浮检测保留在轻量支持对象上
    onEntered: {
        startShowTimer()
    }
    onExited: {
        stopShowTimer()
        if (_popupLoader.item) {
            _popupLoader.item.startHideTimer()
        }
    }

    // ==================== Content 内容 ====================
    Loader {
        id: _popupLoader
        objectName: "_popupLoader"
        anchors.fill: parent
        active: false

        onLoaded: {
            if (!item) return
            if (support.widget && support.widget._toolTipShowPending) item.show()
            else if (support._showScheduled) {
                item.startShowTimer(Math.max(0, Date.now() - support._showRequestedAt))
            }
        }
    }

}
