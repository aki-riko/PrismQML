// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../feedback"
import "../../../../effects"

// SliderDefaultContent - Default slider visuals 默认滑块视觉内容
// Keeps the default track/handle interaction outside SliderCore's mode orchestration.
// 将默认轨道/手柄交互移出 SliderCore 的模式编排。
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var sliderControl

    // ==================== Readonly State 只读状态 ====================
    readonly property bool hovered: handleArea.containsMouse
        || trackArea.containsMouse || wheelArea.containsMouse
    readonly property bool pressed: handleArea.pressed

    // ==================== Size 尺寸 ====================
    anchors.fill: parent

    // ==================== Content 内容 ====================
    // Mouse wheel support 鼠标滚轮支持
    MouseArea {
        id: wheelArea

        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        hoverEnabled: true

        onWheel: (event) => {
            if (!sliderControl.enabled) return
            var delta = event.angleDelta.y / 120 * sliderControl.stepSize
            sliderControl.smoothSetValue(sliderControl.value + delta)
            event.accepted = true
        }
    }

    // Track 轨道
    Rectangle {
        id: track

        anchors.centerIn: parent
        width: sliderControl.isHorizontal ? parent.width : Enums.radius.small
        height: sliderControl.isHorizontal ? Enums.radius.small : parent.height
        radius: sliderControl._trackRadius
        color: sliderControl._trackColor

        NeumorphicShadow {
            target: track
            inset: true
            visible: Enums.isNeumorphism
        }

        // Progress 进度
        Rectangle {
            width: sliderControl.isHorizontal
                ? handle.x + handle.width / 2 : parent.width
            height: sliderControl.isHorizontal
                ? parent.height : parent.height - handle.y - handle.height / 2
            y: sliderControl.isHorizontal ? 0 : handle.y + handle.height / 2
            radius: parent.radius
            color: sliderControl._progressColor
        }

        MouseArea {
            id: trackArea

            anchors.fill: parent
            anchors.margins: -Enums.spacing.m
            enabled: sliderControl.enabled
            hoverEnabled: true
            onClicked: (mouse) => {
                var trackPoint = trackArea.mapToItem(track, mouse.x, mouse.y)
                var span = sliderControl.isHorizontal ? track.width : track.height
                var pos = span > 0
                    ? (sliderControl.isHorizontal
                        ? trackPoint.x / span : 1 - trackPoint.y / span)
                    : 0
                pos = Math.max(0, Math.min(1, pos))
                var newValue = sliderControl.from
                    + pos * (sliderControl.to - sliderControl.from)
                if (sliderControl.stepSize > 0
                        && isFinite(sliderControl.stepSize)) {
                    newValue = Math.round(newValue / sliderControl.stepSize)
                        * sliderControl.stepSize
                }
                newValue = Math.max(
                    sliderControl.from,
                    Math.min(sliderControl.to, newValue)
                )
                sliderControl.value = newValue
                sliderControl.valueModified(newValue)
            }
        }
    }

    // Handle 手柄
    Rectangle {
        id: handle

        // Clamp ratio during transient range changes 在量程瞬时变化时将比例钳制到 [0,1]
        // Prevent the handle from escaping before to/from settle 防止程序改值早于量程更新时手柄越界
        readonly property real _ratio: sliderControl._safePosition(
            sliderControl.value
        )

        width: Enums.controlSize.switchHeight
        height: Enums.controlSize.switchHeight
        radius: width / 2
        x: sliderControl.isHorizontal
            ? _ratio * (track.width - width) + track.x
            : (parent.width - width) / 2
        y: sliderControl.isHorizontal
            ? (parent.height - height) / 2
            : (1 - _ratio) * (track.height - height) + track.y
        color: sliderControl.handleColor
        border.width: sliderControl._handleBorderWidth
        border.color: sliderControl._handleBorderColor

        NeumorphicShadow {
            target: handle
            inset: handleArea.pressed
            visible: Enums.isNeumorphism
            z: handle.z - 1
        }

        Rectangle {
            anchors.centerIn: parent

            // Handle inner circle: shrinks on press, grows on hover 内圆:按下缩小,悬停放大
            width: handleArea.pressed
                ? Enums.iconSize.micro
                : (content.hovered ? Enums.iconSize.xs : Enums.iconSize.tiny)
            height: width
            radius: width / 2
            color: sliderControl._handleInnerColor

            HoverBehavior on width {
                active: content.hovered && !content.pressed
                enterDuration: Enums.duration.fast
                easingType: Easing.OutCubic
            }
        }

        // Create the tooltip on first hover/press, then reuse it.
        // 首次悬停/按下时创建提示，随后复用。
        Loader {
            active: content.hovered || content.pressed || item !== null
            sourceComponent: TooltipCore {
                x: (parent.width - width) / 2
                y: -height - Enums.spacing.m
                text: sliderControl._tipText(sliderControl.value)
                visible: content.hovered || content.pressed
                // Reposition with handle.x during drag or programmatic changes 拖动或程序改值时跟随手柄重定位
                followAnchor: content.hovered || content.pressed
            }
        }

        // Avoid drag.target because it breaks the handle.x binding 避免使用会破坏 handle.x 绑定的 drag.target
        // Map the pointer to value while handle.x stays bound to value 按指针位置映射 value 并保持 handle.x 绑定
        // This keeps programmatic updates and user dragging stable 保证程序更新与用户拖动稳定
        MouseArea {
            id: handleArea

            function _applyFromGlobal(gx, gy) {
                var p = track.mapFromGlobal(gx, gy)
                var span = sliderControl.isHorizontal
                    ? track.width : track.height
                var pos = span > 0
                    ? (sliderControl.isHorizontal
                        ? p.x / span : 1 - p.y / span) : 0
                pos = Math.max(0, Math.min(1, pos))
                var newValue = sliderControl.from
                    + pos * (sliderControl.to - sliderControl.from)
                newValue = sliderControl._maybeSnap(newValue, true)
                newValue = Math.max(
                    sliderControl.from,
                    Math.min(sliderControl.to, newValue)
                )
                if (newValue !== sliderControl.value) {
                    sliderControl.value = newValue
                    sliderControl.valueModified(newValue)
                }
            }

            anchors.fill: parent
            anchors.margins: -Enums.spacing.xs
            enabled: sliderControl.enabled
            hoverEnabled: true
            preventStealing: true

            onPressed: sliderControl._dragging = true
            onReleased: {
                sliderControl._dragging = false
                // Snap after release for SnapOnRelease/SnapAlways 松手后执行吸附
                var snapped = sliderControl._maybeSnap(
                    sliderControl.value, false
                )
                snapped = Math.max(
                    sliderControl.from,
                    Math.min(sliderControl.to, snapped)
                )
                if (snapped !== sliderControl.value) {
                    sliderControl.value = snapped
                    sliderControl.valueModified(snapped)
                }
            }
            onPositionChanged: (mouse) => {
                if (pressed) {
                    var g = mapToGlobal(mouse.x, mouse.y)
                    _applyFromGlobal(g.x, g.y)
                }
            }
        }
    }
}
