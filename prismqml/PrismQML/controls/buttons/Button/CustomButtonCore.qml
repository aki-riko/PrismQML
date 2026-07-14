// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."
import "../../icons"
import "../../../effects"
import "../../data"
import "../../containers"

// CustomButtonCore - Button core with overridable colors and custom content 可覆盖颜色和自定义内容的按钮核心
// Provides overridable color callbacks and custom content for specialized buttons 为专用按钮提供可覆盖颜色回调和自定义内容
Widget {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string text: ""
    property string icon: ""           // Icon name / image path 图标名或图片路径
    property int iconSize: Enums.iconSize.m
    property bool flat: false          // No border 是否无边框
    property int radius_: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small + 1  // Use radius_ to avoid Rectangle.radius conflict 避免冲突
    property bool iconThemeAware: true // Icon follows theme color 图标跟随主题色

    // Text style 文本样式
    readonly property int fontSize: Enums.typography.body

    // Overridable color callbacks 可覆盖颜色回调
    // Default button colors 默认按钮颜色
    property var getBackgroundColor: function() {
        if (!enabled) return Enums.stateColor.controlBgDisabled
        if (pressed) return Enums.stateColor.controlBgPressed
        if (hovered) return Enums.stateColor.controlBgHover
        return Enums.stateColor.controlBg
    }

    property var getBorderColor: function() {
        if (!enabled) return Enums.stateColor.borderLight
        if (hovered) return Enums.stateColor.borderStrong
        return Enums.stateColor.border
    }

    property var getTextColor: function() {
        if (!enabled) return Enums.stateColor.pickerTextDisabled
        if (pressed) return Enums.textColor.pressed
        return Enums.textColor.primary
    }

    // Custom content offset 自定义内容偏移
    property int contentOffsetX: 0  // Horizontal offset, positive = left 水平偏移

    // ==================== Readonly State 只读状态 ====================
    readonly property bool hovered: mouseArea.containsMouse
    readonly property bool pressed: mouseArea.pressed
    // State string (for debug) 状态字符串
    readonly property string buttonState: {
        if (!enabled) return "disabled"
        if (pressed) return "pressed"
        if (hovered) return "hovered"
        return "normal"
    }
    // Check if has icon 判断是否有图标
    readonly property bool hasIcon: icon !== ""

    // ==================== Signals 信号 ====================
    signal clicked()
    // The name pressed would be shadowed by the property; use onButtonPressed externally. pressed 名称会被同名属性遮蔽；外部请使用 onButtonPressed。
    signal buttonPressed()
    signal released()

    // ==================== Size 尺寸 ====================
    // Content size (inherited from Widget) 内容尺寸（继承自Widget）
    contentWidth: Math.max(contentRow.implicitWidth + Enums.spacing.xl, Enums.controlSize.buttonMinWidth)
    contentHeight: Enums.controlSize.inputHeight
    // Disabled opacity 禁用透明度
    opacity: enabled ? 1.0 : 0.6

    // ==================== Content 内容 ====================
    // Shadow layer 阴影层
    // Fluent uses a blurred shadow; Neobrutalism uses a hard shadow. Fluent 使用模糊阴影；Neobrutalism 使用硬阴影。
    RectangularShadow {
        anchors.fill: background
        radius: background.radius
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset.x: 0
        offset.y: Enums.shadow.level2.offset
        visible: !control.flat && !Enums.isNeobrutalism
    }

    NeoShadow {
        target: background
        visible: !control.flat && Enums.isNeobrutalism
        z: background.z - 1
    }

    // Background 背景
    Rectangle {
        id: background
        anchors.fill: parent
        radius: control.radius_
        color: control.getBackgroundColor()
        border.width: control.flat ? 0 : (Enums.isNeobrutalism ? Enums.neo.borderWidth : 1)
        border.color: control.getBorderColor()
        
        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
    }

    // Content row 内容行
    Row {
        id: contentRow
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: -control.contentOffsetX
        spacing: control.hasIcon ? 6 : 0
        
        // Unified icon component 统一图标组件
        Icon {
            id: iconItem
            icon: control.icon
            iconSize: control.iconSize
            color: control.getTextColor()
            themeAware: control.iconThemeAware
            visible: control.hasIcon
            anchors.verticalCenter: parent.verticalCenter
        }
        
        // Text 文字
        Label {
            id: contentText
            type: Enums.label.type_body
            text: control.text
            color: control.getTextColor()
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    // Interaction 交互
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        enabled: control.enabled
        onClicked: control.clicked()
        onPressed: control.buttonPressed()
        onReleased: control.released()
    }
}
