// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// SmoothScrollTrace - Opt-in runtime trace for smooth scroll state 滚动状态显式运行时跟踪
Item {
    id: control

    // ==================== Required Props 必需属性 ====================
    required property Item helper
    required property Flickable target

    // ==================== Internal Props 内部属性 ====================
    property int _sequence: 0
    property real _lastContentX: 0
    property real _lastContentY: 0
    property real _lastContentDeltaX: 0
    property real _lastContentDeltaY: 0
    property string writeSource: ""

    // ==================== Readonly State 只读状态 ====================
    readonly property string _orientationName:
        helper._isVertical ? "vertical" : "horizontal"

    // ==================== Public Methods 公开方法 ====================
    function record(stage, details) {
        if (!enabled) return
        _sequence += 1
        var detailText = details ? " " + details : ""
        console.info("[ScrollBounceTrace]" +
                     " ts=" + Date.now() +
                     " seq=" + _sequence +
                     " helper=" + _quote(_objectLabel(helper)) +
                     " target=" + _quote(_objectLabel(target)) +
                     " stage=" + stage +
                     " orientation=" + _orientationName +
                     " content=" + _number(helper._isVertical
                                             ? target.contentY : target.contentX) +
                     " targetPos=" + _number(helper.targetPos) +
                     " smoothPos=" + _number(helper.smoothPos) +
                     " min=" + _number(helper.minScroll) +
                     " max=" + _number(helper.maxScroll) +
                     " contentSize=" + _number(helper._isVertical
                                                 ? target.contentHeight
                                                 : target.contentWidth) +
                     " viewSize=" + _number(helper._isVertical
                                              ? target.height : target.width) +
                     " overshot=" + helper.isOvershot +
                     " boundary=" + (helper._isVertical
                                      ? helper._bounceBoundaryV
                                      : helper._bounceBoundaryH) +
                     " blocked=" + (helper._isVertical
                                     ? helper._blockedBounceBoundaryV
                                     : helper._blockedBounceBoundaryH) +
                     " bouncePhase=" + helper._bouncePhase +
                     " syncing=" + helper._syncing + detailText)
    }

    function currentWriteSource() {
        if (helper._bouncePhase !== "idle") return "bounce." + helper._bouncePhase
        return helper._syncing ? "sync" : "smooth-animation"
    }

    // ==================== Internal Methods 内部方法 ====================
    function _number(value) {
        return String(Math.round(Number(value) * 1000) / 1000)
    }

    function _quote(value) {
        return JSON.stringify(String(value))
    }

    function _objectLabel(item) {
        if (!item) return "null"
        return item.objectName ? item.objectName : String(item)
    }

    function _resetPositionHistory() {
        _lastContentX = target ? target.contentX : 0
        _lastContentY = target ? target.contentY : 0
        _lastContentDeltaX = 0
        _lastContentDeltaY = 0
    }

    function _observeContent(axis, value) {
        if (!enabled) return
        if (axis !== (helper._isVertical ? "y" : "x")) return
        var previous = axis === "x" ? _lastContentX : _lastContentY
        var previousDelta = axis === "x" ? _lastContentDeltaX : _lastContentDeltaY
        var delta = value - previous
        var reversal = delta !== 0 && previousDelta !== 0 && delta * previousDelta < 0
        if (axis === "x") {
            _lastContentX = value
            if (delta !== 0) _lastContentDeltaX = delta
        } else {
            _lastContentY = value
            if (delta !== 0) _lastContentDeltaY = delta
        }
        record("content.changed", "axis=" + axis +
               " previous=" + _number(previous) +
               " value=" + _number(value) +
               " delta=" + _number(delta) +
               " reversal=" + reversal +
               " source=" + _quote(writeSource || "external"))
    }

    function _recordGeometry(propertyName, value) {
        record("geometry.changed", "property=" + propertyName +
               " value=" + _number(value))
    }

    width: 0
    height: 0
    visible: false

    onEnabledChanged: {
        if (!enabled) return
        _resetPositionHistory()
        record("trace.enabled", "")
    }

    Component.onCompleted: {
        _resetPositionHistory()
        if (enabled) record("trace.enabled", "")
    }

    Connections {
        function onContentXChanged() {
            control._observeContent("x", control.target.contentX)
        }
        function onContentYChanged() {
            control._observeContent("y", control.target.contentY)
        }
        function onContentWidthChanged() {
            control._recordGeometry("contentWidth", control.target.contentWidth)
        }
        function onContentHeightChanged() {
            control._recordGeometry("contentHeight", control.target.contentHeight)
        }
        function onWidthChanged() {
            control._recordGeometry("width", control.target.width)
        }
        function onHeightChanged() {
            control._recordGeometry("height", control.target.height)
        }
        function onOriginXChanged() {
            control._recordGeometry("originX", control.target.originX)
        }
        function onOriginYChanged() {
            control._recordGeometry("originY", control.target.originY)
        }

        target: control.enabled ? control.target : null
    }
}
