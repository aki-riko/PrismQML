// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// SmoothScrollWheelArea - Smooth-scroll wheel input layer 平滑滚轮输入层
//
// This layer is a pointer handler rather than a MouseArea on purpose. A MouseArea
// competes for the wheel as a plain item: with the original z (below the target)
// an interactive Flickable swallows the wheel through Qt's native scrolling path
// before this layer ever sees it, so the smooth animation is lost and only the
// short native easing remains; raising its z instead makes the overlay outrank
// every nested control, so a focused text editor or a nested blocking WheelHandler
// inside the list loses its own wheel. A pointer handler keeps both: Qt gives the
// wheel to the deepest handler first, and `blocking: true` keeps the target's
// native wheel scrolling out of the way without outranking a deeper handler.
// 本层刻意使用指针处理器而非 MouseArea。MouseArea 以普通项参与滚轮竞争: 保持原有 z
// (位于目标之下)时, 可交互 Flickable 会走 Qt 原生滚动路径先吞掉滚轮, 本层收不到,
// 平滑动画退化成短促的原生缓动; 提高 z 则让覆盖层压过所有内嵌控件, 列表内聚焦的
// 文本编辑器或嵌套 blocking WheelHandler 就失去自己的滚轮。指针处理器两者兼顾:
// Qt 会把滚轮先给最深的处理器, 而 `blocking: true` 在不压过更深处理器的前提下
// 阻止目标的原生滚轮滚动。
//
// Note: an explicit hand-off (accepting nothing so a nested control could take the
// wheel) was measured to have no observable effect on any nested surface while it
// broke the Timeline bounce path, because Qt does not re-offer an ignored wheel to a
// deeper item. Nested priority is owned by Qt's handler competition, so this layer
// must not try to re-implement it.
// 备注: 曾尝试显式交还滚轮(不接受事件以便内嵌控件接管)。实测该做法对所有内嵌场景
// 均无可观察影响, 却破坏了时间线的回弹路径, 因为 Qt 不会把已被忽略的滚轮再交给更深
// 的项。内嵌优先权由 Qt 的处理器竞争负责, 本层不应重复实现。
WheelHandler {
    id: wheelArea

    // ==================== Required Props 必需属性 ====================
    required property var scrollHelper

    // Use the target as the native parent so the handler keeps the original
    // hit-test relationship. 使用目标作为原生父级，保持原有命中测试关系。
    parent: scrollHelper.target
    enabled: scrollHelper.handleWheel
    // Stop the target's native wheel scrolling without outranking nested handlers
    // 阻止目标的原生滚轮滚动, 同时不压过更深的处理器
    blocking: true

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
}
