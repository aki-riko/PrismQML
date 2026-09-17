// PipsPagerContent - Pips container and delegate content 点容器与委托内容
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// PipsPagerContent - Owns pips layout, scrolling, and delegates 承载点布局、滚动与委托
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var pagerControl

    clip: true

    anchors {
        left: pagerControl.vertical || !pagerControl._prevButton
              || !pagerControl._prevButton.visible
            ? parent.left : pagerControl._prevButton.right
        right: pagerControl.vertical || !pagerControl._nextButton
               || !pagerControl._nextButton.visible
            ? parent.right : pagerControl._nextButton.left
        top: !pagerControl.vertical || !pagerControl._prevButton
             || !pagerControl._prevButton.visible
            ? parent.top : pagerControl._prevButton.bottom
        bottom: !pagerControl.vertical || !pagerControl._nextButton
                || !pagerControl._nextButton.visible
            ? parent.bottom : pagerControl._nextButton.top
    }

    // ==================== Content 内容 ====================
    // Shared horizontal and vertical pips layout 横竖方向共享点布局
    Item {
        id: pipsLayout

        property real _scrollOffset: {
            if (content.pagerControl.count <= content.pagerControl.maxVisible) return 0
            var centerOffset = content.pagerControl.currentIndex
                               - Math.floor(content.pagerControl.maxVisible / 2)
            var maxOffset = content.pagerControl.count
                            - content.pagerControl.maxVisible
            return Math.max(0, Math.min(centerOffset, maxOffset))
                   * content.pagerControl._cellSize
        }
        property real _animatedScrollOffset: _scrollOffset

        width: content.pagerControl._pipCount > 0
            ? (content.pagerControl.vertical
                ? content.pagerControl._cellSize
                : content.pagerControl._pipCount * content.pagerControl._cellSize)
            : 0
        height: content.pagerControl._pipCount > 0
            ? (content.pagerControl.vertical
                ? content.pagerControl._pipCount * content.pagerControl._cellSize
                : content.pagerControl._cellSize)
            : 0
        x: content.pagerControl.vertical
            ? (parent.width - width) / 2
            : -_animatedScrollOffset
        y: content.pagerControl.vertical
            ? -_animatedScrollOffset
            : (parent.height - height) / 2

        Behavior on _animatedScrollOffset {
            NumberAnimation {
                duration: Enums.duration.medium
                easing.type: Easing.OutCubic
            }
        }

        Repeater {
            model: content.pagerControl._pipCount

            Item {
                // Touch has no hover preview: on touch the hover treatment follows the press
                // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
                readonly property bool _touchActive: Touch.feedback(pipMouse.containsMouse,
                                                                   pipMouse.pressed)

                width: content.pagerControl._cellSize
                height: content.pagerControl._cellSize
                x: content.pagerControl.vertical
                    ? 0 : index * content.pagerControl._cellSize
                y: content.pagerControl.vertical
                    ? index * content.pagerControl._cellSize : 0

                Rectangle {
                    anchors.centerIn: parent
                    width: (index === content.pagerControl.currentIndex
                            || _touchActive)
                        ? content.pagerControl._activeDiameter
                        : content.pagerControl._normalDiameter
                    height: width
                    radius: width / 2
                    color: index === content.pagerControl.currentIndex
                           ? content.pagerControl._pipActiveColor
                           : (_touchActive
                              ? content.pagerControl._pipHoverColor
                              : content.pagerControl._pipInactiveColor)

                    HoverBehavior on width {
                        active: _touchActive
                                && index !== content.pagerControl.currentIndex
                        enterDuration: Enums.duration.fast
                    }
                    HoverBehavior on color {
                        active: _touchActive
                                && index !== content.pagerControl.currentIndex
                        enterDuration: Enums.duration.fast
                    }
                }

                MouseArea {
                    id: pipMouse

                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        if (content.pagerControl.interactive)
                            content.pagerControl.currentIndex = index
                        content.pagerControl.indexClicked(index)
                    }
                }
            }
        }
    }
}
