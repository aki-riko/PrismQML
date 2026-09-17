// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// SmoothScrollWheelArea - Smooth-scroll wheel input layer 平滑滚轮输入层
MouseArea {
    id: wheelArea

    // ==================== Required Props 必需属性 ====================
    required property var scrollHelper

    // Use the target as the native parent so the overlay keeps the original
    // hit-test and clipping relationship. 使用目标作为原生父级，保持原有命中测试与裁剪关系。
    parent: scrollHelper.target
    anchors.fill: parent
    enabled: scrollHelper.handleWheel
    visible: scrollHelper.handleWheel
    acceptedButtons: Qt.NoButton
    propagateComposedEvents: true
    // Keep the wheel layer below the Flickable it overlays. The overlay is a
    // sibling of the target, so any non-negative z outranks the target together
    // with every control nested inside it (focused text editors, spin boxes).
    // That made wheel input skip a nested scrollable input and scroll the outer
    // list instead. Staying below lets nested controls consume the wheel first;
    // the nested-scroll dispatcher still routes unhandled wheel deltas here,
    // so smooth scrolling and native-drag rebasing keep working.
    // 滚轮层保持在所属 Flickable 之下。本覆盖层与目标同级，任何非负 z 都会连同
    // 目标内部的控件(聚焦文本编辑器、SpinBox 等)一起被压过，导致滚轮跳过内层可滚
    // 输入控件而滚动外层列表。置于其下可让内层控件优先消费滚轮；未被消费的滚轮仍由
    // 嵌套滚动调度器转发到此，平滑滚动与原生拖拽重置照常生效。
    z: Enums.zIndex.background

    onWheel: (event) => {
        // Check if scroll is needed 检查是否需要滚动
        var contentSize = scrollHelper.orientation === Qt.Vertical
            ? scrollHelper.target.contentHeight
            : scrollHelper.target.contentWidth
        var viewSize = scrollHelper.orientation === Qt.Vertical
            ? scrollHelper.target.height
            : scrollHelper.target.width
        if (contentSize <= viewSize) {
            event.accepted = false
            return
        }

        scrollHelper.scrollBy(-event.angleDelta.y / 120 * scrollHelper.step)
        event.accepted = true
    }

    onPressed: (event) => event.accepted = false
    onReleased: (event) => event.accepted = false
    onClicked: (event) => event.accepted = false
}
