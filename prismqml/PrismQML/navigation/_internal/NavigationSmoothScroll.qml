// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// NavigationSmoothScroll - Shared smooth wheel behavior for navigation bars 导航栏共享平滑滚轮行为
// Must be placed inside the target Flickable so WheelHandler receives viewport events. 必须放在目标 Flickable 内，以便 WheelHandler 接收视口事件。
Item {
    id: behavior

    // ==================== Required Props 必需属性 ====================
    required property Flickable flickable

    // ==================== Public Props 公开属性 ====================
    property string helperName: "navigationSmoothScrollHelper"
    property bool smoothScroll: true
    property int duration: Enums.duration.navigationScroll
    property real step: Enums.spacing.navigationScrollStep
    property int easing: Easing.OutQuart

    // ==================== Readonly State 只读状态 ====================
    readonly property real targetPos: scrollHelper.targetPos
    readonly property bool _scrollable: flickable.contentHeight > flickable.height

    // ==================== Public Methods 公开方法 ====================
    function scrollTo(targetY) { scrollHelper.scrollTo(targetY) }
    function scrollBy(delta) { scrollHelper.scrollBy(delta) }

    anchors.fill: parent

    // ==================== Content 内容 ====================
    Item {
        id: scrollHelper

        // Keep the helper properties consumed by navigation hosts. 保留导航宿主使用的 helper 属性。
        readonly property int duration: behavior.duration
        readonly property bool handleWheel: false
        readonly property real targetPos: _targetY
        readonly property real maxScroll: _maxY
        readonly property real _minY: behavior.flickable.originY
        readonly property real _maxY:
            _minY + Math.max(0, behavior.flickable.contentHeight - behavior.flickable.height)
        property real _targetY: 0
        property real _smoothY: 0
        property bool _syncing: false

        function _clamp(value, minimum, maximum) {
            return Math.max(minimum, Math.min(maximum, value))
        }

        function scrollTo(targetY) {
            _targetY = _clamp(targetY, _minY, _maxY)
            _smoothY = _targetY
        }

        function scrollBy(delta) {
            scrollTo(_targetY + delta)
        }

        function _reconcileBounds() {
            if (!scrollAnimation.running) {
                var currentY = _clamp(behavior.flickable.contentY, _minY, _maxY)
                if (currentY === _targetY && currentY === _smoothY) return
                _syncing = true
                _targetY = currentY
                _smoothY = currentY
                _syncing = false
                return
            }
            var targetY = _clamp(_targetY, _minY, _maxY)
            var smoothY = _clamp(_smoothY, _minY, _maxY)
            if (targetY === _targetY && smoothY === _smoothY) return
            _targetY = targetY
            if (smoothY !== _smoothY) {
                _syncing = true
                _smoothY = smoothY
                _syncing = false
            }
            if (_smoothY !== _targetY) _smoothY = _targetY
        }

        objectName: behavior.helperName
        enabled: behavior.enabled && behavior.smoothScroll && behavior._scrollable

        on_SmoothYChanged: behavior.flickable.contentY = _smoothY
        on_MinYChanged: reconcileTimer.restart()
        on_MaxYChanged: reconcileTimer.restart()

        Component.onCompleted: {
            _targetY = behavior.flickable.contentY
            _smoothY = behavior.flickable.contentY
        }

        Timer {
            id: reconcileTimer
            interval: Enums.duration.instant
            repeat: false
            onTriggered: scrollHelper._reconcileBounds()
        }

        Behavior on _smoothY {
            enabled: scrollHelper.enabled && !scrollHelper._syncing
            NumberAnimation {
                id: scrollAnimation
                duration: scrollHelper.duration
                easing.type: behavior.easing
            }
        }
    }

    WheelHandler {
        onWheel: (event) => {
            if (!behavior.enabled || !behavior.smoothScroll || !behavior._scrollable) {
                event.accepted = false
                return
            }

            var delta = event.angleDelta.y
            if (delta === 0) {
                event.accepted = false
                return
            }

            scrollHelper.scrollBy(-delta / 120 * behavior.step)
            event.accepted = true
        }
    }
}
