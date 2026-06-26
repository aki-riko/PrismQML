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

// ButtonCore - Button base class 按钮基类
// All button components should extend this 所有按钮组件应继承此基类
// Subclass only needs to override color functions 子类只需覆盖颜色函数
Widget {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string text: ""
    property string icon: ""           // Icon name / image path 图标名或图片路径
    property int iconSize: Enums.iconSize.m
    property bool flat: false          // No border 是否无边框
    property int radius_: Enums.radius.small + 1  // Use radius_ to avoid Rectangle.radius conflict 避免冲突
    property bool iconThemeAware: true // Icon follows theme color 图标跟随主题色
    
    // ==================== Signals 信号 ====================
    signal clicked()
    // 不能命名为 pressed, 会与下方 `property bool pressed` 同名被遮蔽; 外部用 onButtonPressed
    signal buttonPressed()
    signal released()

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
    
    // ==================== Size 尺寸 ====================
    // Content size (inherited from Widget) 内容尺寸（继承自Widget）
    contentWidth: Math.max(contentRow.implicitWidth + Enums.spacing.xl, Enums.controlSize.buttonMinWidth)
    contentHeight: Enums.controlSize.inputHeight
    
    // ==================== Text Style 文本样式 ====================
    readonly property string fontFamily: Enums.fontFamily
    readonly property int fontSize: Enums.typography.body
    
    // ==================== Color Functions (subclass override) 颜色函数 ====================
    
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
    
    // ==================== Content Offset (subclass can set) 内容偏移 ====================
    property int contentOffsetX: 0  // Horizontal offset, positive = left 水平偏移
    
    // ==================== Content 内容 ====================
    // Check if has icon 判断是否有图标
    readonly property bool hasIcon: icon !== ""
    
    // ==================== Shadow Layer 阴影层 ====================
    // Fluent: 模糊阴影; neo: 硬阴影
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

    // ==================== Background 背景 ====================
    Rectangle {
        id: background
        anchors.fill: parent
        radius: control.radius_
        color: control.getBackgroundColor()
        border.width: control.flat ? 0 : (Enums.isNeobrutalism ? Enums.neo.borderWidth : 1)
        border.color: control.getBorderColor()
        
        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
    }
    
    // ==================== Content Row 内容行 ====================
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
    
    // ==================== Interaction 交互 ====================
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        enabled: control.enabled
        onClicked: control.clicked()
        onPressed: control.buttonPressed()
        onReleased: control.released()
    }
    
    // ==================== Disabled State 禁用状态 ====================
    opacity: enabled ? 1.0 : 0.6
}
