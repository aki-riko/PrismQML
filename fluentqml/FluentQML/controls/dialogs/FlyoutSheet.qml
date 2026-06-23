// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../.."
import QtQuick.Effects
import "../../effects"
import "../buttons"
import "../containers"
import "../icons"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖
import QtQuick.Window  // 置于库import后:去前缀后保原生Window不被库覆盖

// FlyoutSheet - Floating dialog 浮动对话框
Window {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var contentItem: null  // Custom content component 自定义内容组件
    property string confirmText: Translator.tr("ok")
    property string cancelText: Translator.tr("cancel")
    property bool showCancelButton: true
    property bool deleteOnClose: true
    
    // ==================== Signals 信号 ====================
    signal accepted()
    signal rejected()
    
    // ==================== Internal State 内部状态 ====================
    property Item targetItem: null
    property bool isOpen: false
    
    width: contentContainer.width + 32
    height: contentContainer.height + buttonRow.height + 48
    visible: false
    flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoFluentShadowWindowHint
    color: Enums.transparent
    
    onActiveFocusItemChanged: {
        if (!activeFocusItem && isOpen) close()
    }

    // ==================== 方法 ====================
    function open(target) {
        if (target) {
            targetItem = target
            var pos = target.mapToGlobal(target.width / 2, target.height + 8)
            control.x = pos.x - control.width / 2
            control.y = pos.y
        }
        control.show()
        control.raise()
        control.requestActivate()
        isOpen = true
    }

    function close() {
        isOpen = false
        control.hide()
        if (deleteOnClose) {
            control.destroy()
        }
    }

    // ==================== Shadow Layer 阴影层 ====================
    // Fluent: 模糊阴影; neo: 硬阴影
    RectangularShadow {
        anchors.fill: container
        radius: container.radius
        color: Enums.shadow.level8.color
        blur: Enums.shadow.level8.blur
        offset: Qt.vector2d(0, Enums.shadow.level8.offset)
        visible: !Enums.isNeobrutalism
    }

    NeoShadow {
        target: container
        visible: Enums.isNeobrutalism
        z: container.z - 1
    }

    // ==================== Main Container 主容器 ====================
    Rectangle {
        id: container
        anchors.fill: parent
        anchors.margins: Enums.spacing.m
        radius: Enums.radius.large
        color: Enums.cardColor
        border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
        border.color: Enums.stateColor.dialogBorder
        
        // Content area 内容区域
        Item {
            id: contentContainer
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: Enums.spacing.xl
            implicitWidth: contentLoader.item ? contentLoader.item.implicitWidth : 200
            implicitHeight: contentLoader.item ? contentLoader.item.implicitHeight : 100
            
            Loader {
                id: contentLoader
                anchors.fill: parent
                sourceComponent: control.contentItem
            }
        }
        
        // Separator 分隔线
        Separator {
            id: separator
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: buttonRow.top
            anchors.bottomMargin: Enums.spacing.l
            anchors.leftMargin: Enums.spacing.xl
            anchors.rightMargin: Enums.spacing.xl
            lineColor: Enums.stateColor.borderLight
        }
        
        // Button area 按钮区域
        Row {
            id: buttonRow
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            anchors.bottomMargin: Enums.spacing.xl
            anchors.rightMargin: Enums.spacing.xl
            spacing: Enums.spacing.l
            
            // Cancel button 取消按钮
            Button {
                text: control.cancelText
                visible: control.showCancelButton
                onClicked: {
                    control.rejected()
                    control.close()
                }
            }
            
            // Confirm button 确定按钮
            Button {
                style: Enums.button.style_primary
                text: control.confirmText
                onClicked: {
                    control.accepted()
                    control.close()
                }
            }
        }
    }

    // ==================== 静态工厂方法 (Fluent Design兼容) ====================
    // Usage: FlyoutSheet.make(view, targetItem, parent) 使用方式
}
