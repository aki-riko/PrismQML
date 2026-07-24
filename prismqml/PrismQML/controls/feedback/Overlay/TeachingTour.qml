// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../../effects"
import "../../utils/_internal"
import "../Tooltip"
import QtQuick.Window  // Keep native Window attached properties unshadowed 保持原生Window附加属性不被遮蔽

// TeachingTour - Multi-step onboarding tour with an inverse opacity mask 反向透明蒙版式多步骤新手指引
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var steps: []
    property Item overlayTarget: null
    property color maskColor: Enums.stateColor.maskHeavy
    property color highlightBorderColor: Enums.accentColor
    property real highlightPadding: Enums.spacing.m
    property real highlightRadius: Enums.radius.large
    property bool blockOutsideInput: true
    property string nextButtonText: { _translationVersion; return Translator.tr("next") }
    property string finishButtonText: { _translationVersion; return Translator.tr("finish") }
    property string skipButtonText: { _translationVersion; return Translator.tr("skip") }
    readonly property int currentIndex: _currentIndex
    readonly property var currentStep: _currentIndex >= 0 && steps &&
                                       typeof steps.length === "number" &&
                                       _currentIndex < steps.length
                                       ? steps[_currentIndex] : null
    readonly property bool active: _active
    readonly property rect spotlightRect: Qt.rect(
        _holeLeft, _holeTop, _holeRight - _holeLeft, _holeBottom - _holeTop)

    // ==================== Internal Props 内部属性 ====================
    property int _currentIndex: -1
    property bool _active: false
    property Item _originalParent: null
    property real _targetX: 0
    property real _targetY: 0
    property real _targetWidth: 0
    property real _targetHeight: 0
    property bool _targetAvailable: false
    readonly property int _translationVersion: Translator._v
    readonly property var _currentTarget: currentStep && currentStep.target !== undefined
                                          ? currentStep.target : null
    readonly property var _targetWindow: _currentTarget && _currentTarget.contentItem !== undefined
                                         ? _currentTarget
                                         : (_currentTarget ? _currentTarget.Window.window : null)
    readonly property bool _isLastStep: currentIndex >= 0 && steps &&
                                        typeof steps.length === "number" &&
                                        currentIndex === steps.length - 1
    readonly property int _currentAnchorPosition: _stepValue(
        "anchorPosition", Enums.teachingTip.anchor_bottom)
    readonly property real _currentHighlightPadding: _stepValue(
        "highlightPadding", highlightPadding)
    readonly property real _currentHighlightRadius: _stepValue(
        "highlightRadius", highlightRadius)
    readonly property real _holeLeft: Math.max(Enums.spacing.none, Math.min(width, _targetX))
    readonly property real _holeTop: Math.max(Enums.spacing.none, Math.min(height, _targetY))
    readonly property real _holeRight: Math.max(_holeLeft, Math.min(width, _targetX + _targetWidth))
    readonly property real _holeBottom: Math.max(_holeTop, Math.min(height, _targetY + _targetHeight))

    // ==================== Signals 信号 ====================
    signal started()
    signal stepChanged(int index, var step)
    signal skipped(int index)
    signal completed()
    signal failed(int index, string reason)

    // ==================== Public Methods 公开方法 ====================
    function start(startIndex) {
        var requestedIndex = startIndex === undefined ? 0 : Math.floor(startIndex)
        if (!steps || typeof steps.length !== "number" || steps.length === 0) {
            _fail(requestedIndex, "TeachingTour requires at least one step")
            return false
        }
        if (requestedIndex < 0 || requestedIndex >= steps.length) {
            _fail(requestedIndex, "TeachingTour start index is out of range")
            return false
        }
        if (!_isUsableStep(steps[requestedIndex])) {
            _fail(requestedIndex, "TeachingTour step target is unavailable")
            return false
        }

        restoreTimer.stop()
        if (!_originalParent) _originalParent = control.parent
        var resolvedTarget = _resolveOverlayTarget()
        if (!resolvedTarget) {
            _fail(requestedIndex, "TeachingTour cannot resolve an overlay target")
            return false
        }
        if (control.parent !== resolvedTarget) control.parent = resolvedTarget

        _currentIndex = requestedIndex
        _active = true
        started()
        stepChanged(_currentIndex, currentStep)
        _showCurrentStep()
        return true
    }

    function next() {
        if (!_active) return
        if (_isLastStep) {
            finish()
            return
        }

        var nextIndex = _currentIndex + 1
        if (!_isUsableStep(steps[nextIndex])) {
            _fail(nextIndex, "TeachingTour step target is unavailable")
            return
        }
        _currentIndex = nextIndex
        stepChanged(_currentIndex, currentStep)
        _showCurrentStep()
    }

    function skip() {
        if (!_active) return
        var skippedIndex = _currentIndex
        _deactivate()
        skipped(skippedIndex)
    }

    function finish() {
        if (!_active) return
        _deactivate()
        completed()
    }

    function stop() {
        if (_active) _deactivate()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _stepValue(name, fallbackValue) {
        if (!currentStep || currentStep[name] === undefined || currentStep[name] === null) {
            return fallbackValue
        }
        return currentStep[name]
    }

    function _isUsableStep(step) {
        return step && step.target && step.target.mapToGlobal !== undefined &&
               typeof step.target.width === "number" &&
               typeof step.target.height === "number"
    }

    function _resolveOverlayTarget() {
        if (overlayTarget) return overlayTarget
        if (Window.window && Window.window.contentItem) return Window.window.contentItem
        return null
    }

    function _refreshSpotlight() {
        if (!_active || !_currentTarget || _currentTarget.mapToGlobal === undefined) return false
        if (_currentTarget.visible !== undefined && !_currentTarget.visible) {
            _handleTargetUnavailable()
            return false
        }

        var globalPosition = _currentTarget.mapToGlobal(Enums.spacing.none, Enums.spacing.none)
        var localPosition = control.mapFromGlobal(globalPosition.x, globalPosition.y)
        _targetX = localPosition.x - _currentHighlightPadding
        _targetY = localPosition.y - _currentHighlightPadding
        _targetWidth = _currentTarget.width + _currentHighlightPadding * 2
        _targetHeight = _currentTarget.height + _currentHighlightPadding * 2
        _targetAvailable = true
        return true
    }

    function _pointInsideSpotlight(point) {
        if (!_targetAvailable || point.x < _holeLeft || point.x > _holeRight ||
                point.y < _holeTop || point.y > _holeBottom) return false

        var holeWidth = _holeRight - _holeLeft
        var holeHeight = _holeBottom - _holeTop
        var radius = Math.max(Enums.radius.none, Math.min(
            _currentHighlightRadius, holeWidth / 2, holeHeight / 2))
        if (radius === Enums.radius.none) return true

        var localX = point.x - _holeLeft
        var localY = point.y - _holeTop
        if (localX >= radius && localX <= holeWidth - radius) return true
        if (localY >= radius && localY <= holeHeight - radius) return true

        var centerX = localX < radius ? radius : holeWidth - radius
        var centerY = localY < radius ? radius : holeHeight - radius
        var deltaX = localX - centerX
        var deltaY = localY - centerY
        return deltaX * deltaX + deltaY * deltaY <= radius * radius
    }

    function _showCurrentStep() {
        var scheduledIndex = _currentIndex
        Qt.callLater(function() {
            if (!_active || _currentIndex !== scheduledIndex) return
            if (!_refreshSpotlight()) return
            stepTip.show()
        })
    }

    function _handleTargetUnavailable() {
        if (!_active) return
        _targetAvailable = false
        _fail(_currentIndex, "TeachingTour step target moved out of view")
    }

    function _deactivate() {
        _active = false
        _targetAvailable = false
        stepTip.close()
        restoreTimer.restart()
    }

    function _fail(index, reason) {
        console.warn(reason, "index:", index)
        if (_active) _deactivate()
        failed(index, reason)
    }

    function _restoreParent() {
        if (_active) return
        if (_originalParent && control.parent !== _originalParent) control.parent = _originalParent
        _currentIndex = -1
    }

    anchors.fill: parent
    z: Enums.zIndex.overlay
    visible: _active

    onWidthChanged: if (_active) Qt.callLater(control._refreshSpotlight)
    onHeightChanged: if (_active) Qt.callLater(control._refreshSpotlight)

    // ==================== Content 内容 ====================
    Rectangle {
        id: inverseMaskSource

        anchors.fill: parent
        color: Enums.transparent
        visible: false
        layer.enabled: true

        Rectangle {
            x: control._holeLeft
            y: control._holeTop
            width: control._holeRight - control._holeLeft
            height: control._holeBottom - control._holeTop
            radius: control._currentHighlightRadius
            color: Enums.textColor.primary
            visible: control._targetAvailable
        }
    }

    Rectangle {
        id: maskSurface

        objectName: "teachingTourMaskSurface"
        anchors.fill: parent
        color: control.maskColor
        layer.enabled: true
        layer.effect: OpacityMask {
            invert: true
            mask: inverseMaskSource
        }
    }

    MouseArea {
        objectName: "teachingTourScrimArea"
        anchors.fill: parent
        enabled: control.blockOutsideInput
        hoverEnabled: true
        acceptedButtons: Qt.AllButtons
        containmentMask: QtObject {
            function contains(point: point): bool {
                return !control._pointInsideSpotlight(point)
            }
        }
        onWheel: (wheel) => wheel.accepted = true
    }

    Rectangle {
        objectName: "teachingTourHighlight"
        x: control._holeLeft
        y: control._holeTop
        width: control._holeRight - control._holeLeft
        height: control._holeBottom - control._holeTop
        radius: control._currentHighlightRadius
        color: Enums.transparent
        border.width: Enums.border.normal
        border.color: control.highlightBorderColor
        visible: control._targetAvailable
    }

    TeachingTip {
        id: stepTip

        objectName: "teachingTourTip"
        target: control._currentTarget
        title: control._stepValue("title", "")
        content: control._stepValue("content", "")
        anchorPosition: control._currentAnchorPosition
        primaryButtonText: control._isLastStep
                           ? control.finishButtonText : control.nextButtonText
        secondaryButtonText: control.skipButtonText
        closeOnAction: false
        closable: false
        modal: false
        duration: Enums.duration.persistent
        deleteOnClose: false
        onPrimaryActionTriggered: control.next()
        onSecondaryActionTriggered: control.skip()
    }

    PopupPositionTracker {
        target: control._currentTarget
        targetWindow: control._targetWindow
        trackingEnabled: control._active
        positionEpsilon: Enums.popupMetrics.positionEpsilon
        onTargetMoved: control._refreshSpotlight()
        onTargetOutOfView: control._handleTargetUnavailable()
    }

    Timer {
        id: restoreTimer

        interval: Enums.duration.tipHide
        repeat: false
        onTriggered: control._restoreParent()
    }
}
