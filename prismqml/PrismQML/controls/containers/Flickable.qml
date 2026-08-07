// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "ScrollBar"

// Flickable - Basic scrollable container 基础可滚动容器
// For Python-side ScrollBar demo Python侧ScrollBar演示用
Flickable {
    id: control

    // ==================== Public Props 公开属性 ====================
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    property int orientation: Qt.Vertical

    // ==================== Public Methods 公开方法 ====================
    function smoothScrollTo(position) { scrollHelper.scrollTo(position) }
    function smoothScrollBy(delta) { scrollHelper.scrollBy(delta) }
    function scrollToStart() { scrollHelper.scrollToStart() }
    function scrollToEnd() { scrollHelper.scrollToEnd() }

    // ==================== Internal Methods 内部方法 ====================
    function _handleSmoothWheel(event) {
        var contentSize = orientation === Qt.Vertical ? contentHeight : contentWidth
        var viewportSize = orientation === Qt.Vertical ? height : width
        if (!smoothScroll || contentSize <= viewportSize) {
            event.accepted = false
            return
        }
        scrollHelper.scrollBy(-event.angleDelta.y / 120 * scrollStep)
        event.accepted = true
    }
    
    // Default size 默认尺寸
    implicitWidth: 200
    implicitHeight: 150
    
    // Clip content 裁剪内容
    clip: true
    
    // Bounce effect 回弹效果
    boundsBehavior: Flickable.StopAtBounds

    // ==================== Content 内容 ====================
    SmoothScrollHelper {
        id: scrollHelper

        target: control
        orientation: control.orientation
        enabled: control.smoothScroll
        duration: control.scrollDuration
        step: control.scrollStep
        easing: control.scrollEasing
        bounceEnabled: false
    }

    Connections {
        function onMovementEnded() { scrollHelper.syncPosition() }
        target: control
    }

    MouseArea {
        id: smoothWheelArea
        parent: control
        anchors.fill: parent
        z: Enums.zIndex.controlsAbove
        acceptedButtons: Qt.NoButton
        propagateComposedEvents: true
        enabled: control.smoothScroll
        onWheel: (event) => control._handleSmoothWheel(event)
    }
}
