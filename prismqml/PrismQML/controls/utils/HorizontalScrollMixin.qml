// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../.."
import "../containers/ScrollBar"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// HorizontalScrollMixin - 横向滚动 mixin
// 给一个 Flickable (ListView 也是 Flickable) target 自动加上:
//   - 横向 SmoothScrollHelper (平滑动画 + overshoot bounce)
//   - 横向 ScrollBar (位于 target 底部)
//   - Shift + 鼠标滚轮 → 横向滚动
//   - 自动启用 horizontal flick (contentWidth > width 时)
//   - 可选: header 容器 x 偏移跟随 target.contentX (表头同步横向滚动)
//
// 使用 Usage:
//   HorizontalScrollMixin {
//       target: listView
//       headerContainer: headerItem   // 可选
//   }
//
// 设计 Design:
//   - parent 默认锚到 target 父级, 显示横向 ScrollBar
//   - 不修改 target 自身代码 (除自动设 flickableDirection / boundsBehavior)
//   - 与 ViewportMixin 风格一致 (utils 目录, 通过 attach 添加能力)
Item {
    id: mixin

    // ==================== 必需 Required ====================
    required property Flickable target

    // ==================== 可选 Optional ====================
    // header 容器: 用于让 header 子内容跟随 target.contentX 横向偏移保持对齐.
    // mixin 会把 headerContainer.x 绑定为 -target.contentX (仅当横向滚动激活时).
    // 不设则 mixin 不管 header.
    property Item headerContainer: null

    // 滚动配置 (与 SmoothScrollHelper 同名属性透传)
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    property bool bounceEnabled: true
    property int barWidth: Enums.spacing.s

    // ==================== 输出 Output ====================
    readonly property bool active: target && target.contentWidth > target.width

    // mixin 自身不占空间, 子项 (ScrollBar / wheelArea) anchors 到 target 父级
    parent: target ? target.parent : null
    anchors.fill: parent ? parent : undefined
    z: Enums.zIndex.controlsAbove

    onTargetChanged: _applyTargetSetup()
    Component.onCompleted: _applyTargetSetup()

    function _applyTargetSetup() {
        if (!target) return
        // 启用 horizontal flick (target 仅作 vertical 时也保留 vertical)
        if (target.flickableDirection !== undefined) {
            target.flickableDirection = Flickable.HorizontalAndVerticalFlick
        }
        // 软边界, 程序化 contentX 设负数才能 overshoot
        if (target.boundsBehavior !== undefined &&
            target.boundsBehavior === Flickable.StopAtBounds) {
            target.boundsBehavior = Flickable.DragAndOvershootBounds
        }
    }

    // ==================== Helper ====================
    SmoothScrollHelper {
        id: hHelper
        target: mixin.target
        orientation: Qt.Horizontal
        enabled: mixin.smoothScroll && mixin.active
        duration: mixin.scrollDuration
        step: mixin.scrollStep
        easing: mixin.scrollEasing
        bounceEnabled: mixin.bounceEnabled
    }

    // ==================== Wheel: Shift + 滚轮 → 横向 ====================
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        propagateComposedEvents: true
        z: Enums.zIndex.background
        onWheel: (event) => {
            if (!mixin.active) {
                event.accepted = false
                return
            }
            if (event.modifiers & Qt.ShiftModifier) {
                var dx = event.angleDelta.x !== 0 ? event.angleDelta.x : event.angleDelta.y
                hHelper.scrollBy(-dx / 120 * hHelper.step)
                event.accepted = true
            } else if (event.angleDelta.x !== 0) {
                // 横向硬件滚轮 (触摸板水平滑动) 直接横向滚
                hHelper.scrollBy(-event.angleDelta.x / 120 * hHelper.step)
                event.accepted = true
            } else {
                event.accepted = false
            }
        }
    }

    // ==================== Header 偏移同步 ====================
    Binding {
        target: mixin.headerContainer
        property: "x"
        value: mixin.active && mixin.target ? -mixin.target.contentX : 0
        when: mixin.headerContainer !== null
    }

    // ==================== Scrollbar ====================
    ScrollBar {
        anchors.left: parent ? parent.left : undefined
        anchors.right: parent ? parent.right : undefined
        anchors.bottom: parent ? parent.bottom : undefined
        anchors.bottomMargin: Enums.spacing.xxs

        target: mixin.target
        scrollHelper: hHelper
        orientation: Qt.Horizontal
        barWidth: mixin.barWidth
        visible: mixin.active
        z: Enums.zIndex.controlsAbove
    }
}
