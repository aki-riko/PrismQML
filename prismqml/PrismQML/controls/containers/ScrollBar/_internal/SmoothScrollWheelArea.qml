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
    propagateComposedEvents: true
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
