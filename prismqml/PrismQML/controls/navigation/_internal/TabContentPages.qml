// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// TabContentPages - Lazy tab page content and slide lifecycle
// TabContentPages - 标签页内容懒加载与滑动生命周期
Rectangle {
    id: contentArea

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Size 尺寸 ====================
    color: Enums.cardColor
    clip: true

    // ==================== Content 内容 ====================
    Repeater {
        model: contentArea.host._safeTabs

        Loader {
            id: pageLoader

            readonly property bool isCurrent: index === contentArea.host.currentIndex
            property bool _animatingOut: false

            width: contentArea.width
            height: contentArea.height
            y: 0
            sourceComponent: (modelData && modelData.content &&
                              typeof modelData.content === "object")
                             ? modelData.content : null

            // Keep the outgoing page active until its slide animation completes.
            // 保持滑出页面 active，直到滑动动画完成后再卸载。
            active: isCurrent || _animatingOut
            visible: active

            // Film-strip layout: the current page is at x=0.
            // 胶片模型：当前页位于 x=0，其余页面按索引横向排列。
            x: (index - contentArea.host.currentIndex) * contentArea.width

            Behavior on x {
                enabled: !contentArea.host._dragging
                NumberAnimation {
                    duration: Enums.duration.slow
                    easing.type: Easing.OutCubic
                    onRunningChanged: {
                        if (!running && !pageLoader.isCurrent) pageLoader._animatingOut = false
                    }
                }
            }

            // Mark the old page as animating out when selection changes.
            // 选中项切换时标记旧页面，维持其内容直到动画结束。
            onIsCurrentChanged: if (!isCurrent) _animatingOut = true
        }
    }
}
