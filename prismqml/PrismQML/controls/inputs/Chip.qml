// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../.."
import "../icons"
import "../buttons"
import "../data"
import "../../effects"
import "../data/Label"

// Chip - Toggle chip with icon, text and close button 可切换的芯片标签
// Similar to ToggleButton logic 类似ToggleButton逻辑
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string text: ""                    // Chip text 芯片文字
    property string icon: ""                    // Icon name / image path 图标名或图片路径
    property bool closable: true                // Show close button 显示关闭按钮
    property bool checked: false                // Toggle state 选中状态

    // ==================== Signals 信号 ====================
    signal clicked()                            // Chip clicked 点击
    signal toggled(bool checked)                // Toggle state changed 切换状态改变
    signal dismissed()                          // Close button clicked 关闭按钮点击
    
    // ==================== Public Methods 公共方法 ====================
    property bool checkable: true               // Whether chip is checkable 是否可选中
    
    
    // Get checked state 获取选中状态
    function isChecked() {
        return checked
    }
    

    // ==================== Private Props 私有属性 ====================
    readonly property bool hovered: mouseArea.containsMouse
    readonly property bool pressed: mouseArea.pressed
    readonly property color contentColor: checked ? Enums.chipColors.checkedText : Enums.foregroundColor

    // ==================== Size 尺寸 ====================
    implicitWidth: row.implicitWidth + Enums.spacing.l * 2
    implicitHeight: 32

    // ==================== Shadow Layer 阴影层 ====================
    // Fluent: 模糊阴影; neo: 硬阴影
    RectangularShadow {
        anchors.fill: chipBg
        radius: chipBg.radius
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset.x: 0
        offset.y: Enums.shadow.level2.offset
        visible: !Enums.isNeobrutalism
    }

    NeoShadow {
        target: chipBg
        visible: Enums.isNeobrutalism
        z: chipBg.z - 1
    }

    // ==================== Background 背景 ====================
    Rectangle {
        id: chipBg
        anchors.fill: parent
        radius: Enums.isNeobrutalism ? Enums.neo.radius : Enums.radius.small

        color: {
            if (checked) return Enums.accentColor
            if (pressed) return Enums.stateColor.chipBgPressed
            if (hovered) return Enums.stateColor.chipBgHover
            return Enums.stateColor.chipBg
        }

        // neo: 选中态也保留黑边(结构差异); Fluent 选中无边
        border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : (checked ? 0 : Enums.border.thin)
        border.color: Enums.stateColor.border

        // ==================== Animations 动画 ====================
        Behavior on color {
            ColorAnimation { duration: Enums.duration.fast }
        }
        Behavior on border.width {
            NumberAnimation { duration: Enums.duration.fast }
        }
    }
    
    // Toggle bounce animation 切换弹跳动画
    ToggleAnimation {
        target: control
        running: control.checked
    }

    // ==================== Interaction 交互 ====================
    // Must be before content so close button can receive clicks 必须在内容之前以便关闭按钮能接收点击
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: {
            if (control.checkable) {
                control.checked = !control.checked
                control.toggled(control.checked)
            }
            control.clicked()
        }
    }

    // ==================== Content 内容 ====================
    Row {
        id: row
        anchors.centerIn: parent
        spacing: Enums.spacing.xs

        // Icon 图标
        Icon {
            iconSize: Enums.iconSize.s
            color: control.contentColor
            visible: control.icon !== ""
            icon: control.icon
            anchors.verticalCenter: parent.verticalCenter
            Behavior on color {
                ColorAnimation { duration: Enums.duration.fast }
            }
        }

        // Text 文字
        Label {
            type: Enums.label.type_body
            text: control.text
            color: control.contentColor
            anchors.verticalCenter: parent.verticalCenter
            Behavior on color {
                ColorAnimation { duration: Enums.duration.fast }
            }
        }

        // Close button 透明关闭按钮
        CloseButton {
            id: closeBtn
            size: Enums.iconSize.m
            iconSizeValue: Enums.iconSize.s
            normalIconColor: control.contentColor
            hoverIconColor: control.contentColor
            hoverBgColor: control.checked ? Enums.stateColor.onAccentOverlay : Enums.stateColor.chipCloseHover
            pressedBgColor: control.checked ? Enums.stateColor.whiteOverlayPressed : Enums.stateColor.chipClosePressed
            visible: control.closable
            anchors.verticalCenter: parent.verticalCenter
            onClicked: { control.dismissed() }
        }
    }
}
