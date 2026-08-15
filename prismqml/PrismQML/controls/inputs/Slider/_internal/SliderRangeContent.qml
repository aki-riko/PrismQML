// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../feedback"
import "../../../../effects"

// SliderRangeContent - Range slider visuals 范围滑块视觉内容
// Keeps range handles and drag mapping outside SliderCore's mode orchestration.
// 将范围句柄与拖动映射移出 SliderCore 的模式编排。
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var sliderControl

    // ==================== Readonly State 只读状态 ====================
    readonly property real firstPos: sliderControl._safePosition(
        sliderControl.firstValue
    )
    readonly property real secondPos: sliderControl._safePosition(
        sliderControl.secondValue
    )

    // ==================== Size 尺寸 ====================
    anchors.fill: parent

    // ==================== Content 内容 ====================
    Rectangle {
        id: groove

        anchors.centerIn: parent
        width: sliderControl.isHorizontal ? parent.width : Enums.radius.small
        height: sliderControl.isHorizontal ? Enums.radius.small : parent.height
        radius: sliderControl._trackRadius
        color: sliderControl._trackColor
    }

    Rectangle {
        x: sliderControl.isHorizontal
            ? groove.x + groove.width * Math.min(content.firstPos, content.secondPos)
            : groove.x
        y: sliderControl.isHorizontal
            ? groove.y
            : groove.y + groove.height * (1 - Math.max(content.firstPos, content.secondPos))
        width: sliderControl.isHorizontal
            ? groove.width * Math.abs(content.secondPos - content.firstPos)
            : Enums.radius.small
        height: sliderControl.isHorizontal
            ? Enums.radius.small
            : groove.height * Math.abs(content.secondPos - content.firstPos)
        radius: sliderControl._trackRadius
        color: sliderControl._progressColor
    }

    RangeHandle {
        handleValue: sliderControl.firstValue
        onValueChanged: (v) => {
            sliderControl.firstValue = v
            sliderControl.sliderMoved(
                sliderControl.firstValue, sliderControl.secondValue
            )
        }
    }

    RangeHandle {
        handleValue: sliderControl.secondValue
        onValueChanged: (v) => {
            sliderControl.secondValue = v
            sliderControl.sliderMoved(
                sliderControl.firstValue, sliderControl.secondValue
            )
        }
    }

    component RangeHandle: Rectangle {
        id: rangeHandle

        property real handleValue: 0

        signal valueChanged(real v)

        width: Enums.controlSize.switchHeight
        height: Enums.controlSize.switchHeight
        radius: width / 2
        x: sliderControl.isHorizontal
            ? Math.max(
                0,
                Math.min(
                    parent.width - width,
                    (parent.width - width)
                        * sliderControl._safePosition(handleValue)
                )
            )
            : (parent.width - width) / 2
        y: sliderControl.isHorizontal
            ? (parent.height - height) / 2
            : Math.max(
                0,
                Math.min(
                    parent.height - height,
                    (parent.height - height)
                        * (1 - sliderControl._safePosition(handleValue))
                )
            )
        color: sliderControl.handleColor
        border.width: sliderControl._handleBorderWidth
        border.color: sliderControl._handleBorderColor

        Rectangle {
            anchors.centerIn: parent

            // Handle inner circle: shrinks on press, grows on hover 内圆:按下缩小,悬停放大
            width: rangeHandleArea.pressed
                ? Enums.iconSize.micro
                : (rangeHandleArea.containsMouse
                    ? Enums.iconSize.xs : Enums.iconSize.tiny)
            height: width
            radius: width / 2
            color: sliderControl._handleInnerColor

            HoverBehavior on width {
                active: rangeHandleArea.containsMouse
                    && !rangeHandleArea.pressed
                enterDuration: Enums.duration.fast
                easingType: Easing.OutCubic
            }
        }

        Loader {
            active: rangeHandleArea.containsMouse
                || rangeHandleArea.pressed || item !== null
            sourceComponent: TooltipCore {
                x: (parent.width - width) / 2
                y: -height - Enums.spacing.m
                text: sliderControl.displayValueFn
                    ? sliderControl.displayValueFn(handleValue)
                    : Math.round(handleValue).toString()
                visible: rangeHandleArea.containsMouse
                    || rangeHandleArea.pressed
                followAnchor: rangeHandleArea.containsMouse
                    || rangeHandleArea.pressed
            }
        }

        MouseArea {
            id: rangeHandleArea

            anchors.fill: parent
            hoverEnabled: true
            drag.target: parent
            drag.axis: sliderControl.isHorizontal ? Drag.XAxis : Drag.YAxis
            drag.minimumX: 0
            drag.maximumX: Math.max(0, parent.parent.width - parent.width)
            drag.minimumY: 0
            drag.maximumY: Math.max(0, parent.parent.height - parent.height)
            enabled: sliderControl.enabled
            preventStealing: true

            onPositionChanged: {
                var available = sliderControl.isHorizontal
                    ? parent.parent.width - parent.width
                    : parent.parent.height - parent.height
                var pos = available > 0
                    ? (sliderControl.isHorizontal
                        ? sliderControl._safeTrackPosition(parent.x, available)
                        : 1 - sliderControl._safeTrackPosition(
                            parent.y, available
                        ))
                    : 0
                pos = Math.max(0, Math.min(1, pos))
                var newVal = sliderControl.from
                    + pos * (sliderControl.to - sliderControl.from)
                if (sliderControl.stepSize > 0
                        && isFinite(sliderControl.stepSize)) {
                    newVal = Math.round(newVal / sliderControl.stepSize)
                        * sliderControl.stepSize
                }
                rangeHandle.valueChanged(newVal)
            }
        }
    }
}
