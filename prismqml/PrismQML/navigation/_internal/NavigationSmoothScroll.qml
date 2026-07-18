// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../../controls/containers/ScrollBar"

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
    SmoothScrollHelper {
        id: scrollHelper
        objectName: behavior.helperName
        target: behavior.flickable
        orientation: Qt.Vertical
        duration: behavior.duration
        step: behavior.step
        easing: behavior.easing
        enabled: behavior.enabled && behavior.smoothScroll && behavior._scrollable
        bounceEnabled: false
        handleWheel: false
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
