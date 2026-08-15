// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."
import "../../../effects"
import "../../data"
import ".."

// PinInputCell - PIN input cell delegate PIN 输入单元格委托
// Keeps cell visuals and hover/focus interaction outside PinInput orchestration.
// 将单元格视觉与悬停/聚焦交互从 PinInput 编排中分离。
Item {
    id: cellItem

    // ==================== Required Props 必需属性 ====================
    required property var pinControl
    required property int index

    // ==================== Internal Props 内部属性 ====================
    property bool hasValue: index < pinControl.value.length
    property bool isCurrentCell: pinControl.focused && index === pinControl.value.length
    property bool hovered: cellMouseArea.containsMouse
    property bool selected: pinControl._isCellSelected(index)

    // ==================== Size 尺寸 ====================
    width: Enums.controlSize.pinBoxCellSize
    height: Enums.controlSize.pinBoxCellSize

    // ==================== Content 内容 ====================
    // Fluent: soft shadow; neo: hard shadow Fluent: 模糊阴影；neo: 硬阴影
    RectangularShadow {
        anchors.fill: pinCell
        radius: pinCell.radius
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset.x: Enums.spacing.none
        offset.y: Enums.shadow.level2.offset
        visible: Enums.usesSoftElevation && !Enums.isNeumorphism
    }

    NeumorphicShadow {
        target: pinCell
        inset: true
        visible: Enums.isNeumorphism
        z: pinCell.z - 1
    }

    NeoShadow {
        target: pinCell
        visible: Enums.isNeobrutalism
        z: pinCell.z - 1
    }

    Rectangle {
        id: pinCell
        anchors.fill: parent
        radius: pinControl._cellRadius

        // Fluent: default/hover/current states Fluent: 默认/悬停/当前格状态
        color: {
            if (!pinControl.enabled) return Enums.stateColor.controlBgDisabled
            if (cellItem.selected) return Enums.accentColor
            if (cellItem.isCurrentCell) return Enums.cardColor
            if (cellItem.hovered) return Enums.stateColor.controlBgHover
            return Enums.stateColor.controlBg
        }

        border.width: pinControl._cellBorderWidth
        border.color: {
            if (cellItem.selected) return Enums.accentColor
            if (Enums.hasOutlinedSurfaces) return cellItem.isCurrentCell ? Enums.accentColor : Enums.stateColor.border
            if (!pinControl.enabled) return Enums.stateColor.borderLight
            if (cellItem.hovered) return Enums.stateColor.borderStrong
            return Enums.stateColor.inputBorderNormal
        }

        HoverBehavior on color {
            active: cellItem.hovered && !cellItem.isCurrentCell && !cellItem.selected
            enterDuration: Enums.duration.fast
        }
        HoverBehavior on border.color {
            active: cellItem.hovered && !cellItem.isCurrentCell && !cellItem.selected
            enterDuration: Enums.duration.fast
        }

        // Display content 显示内容
        Label {
            anchors.centerIn: parent
            type: pinControl.password ? Enums.label.type_title : Enums.label.type_subtitle
            text: cellItem.hasValue ? (pinControl.password ? Enums.input.pinMaskCharacter : pinControl.value.charAt(index)) : ""
            color: cellItem.selected ? Enums.accentForeground
                : (pinControl.enabled ? Enums.textColor.primary : Enums.textColor.disabled)
        }

        // Cursor (only in current cell) 光标（仅当前格）
        Rectangle {
            id: cursor
            anchors.centerIn: parent
            width: Enums.border.medium
            height: Enums.spacing.xxl
            color: Enums.accentColor
            visible: cellItem.isCurrentCell
            opacity: Enums.opacityLevel.visible

            SequentialAnimation on opacity {
                running: cellItem.isCurrentCell
                loops: Animation.Infinite
                NumberAnimation { to: Enums.opacityLevel.invisible; duration: Enums.duration.slower }
                NumberAnimation { to: Enums.opacityLevel.visible; duration: Enums.duration.slower }
            }
        }

        // Focus line (Fluent) 聚焦底线（Fluent）
        FocusLine {
            showLine: cellItem.isCurrentCell
            parentRadius: pinCell.radius
        }
    }

    // Per-cell hover detection 单元格悬停检测
    MouseArea {
        id: cellMouseArea
        anchors.fill: parent
        hoverEnabled: pinControl.enabled
        onClicked: pinControl._focusInput()
    }
}
