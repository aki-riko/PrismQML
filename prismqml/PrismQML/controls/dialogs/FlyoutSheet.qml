// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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
    property string confirmText: { Translator._v; return Translator.tr("ok") }
    property string cancelText: { Translator._v; return Translator.tr("cancel") }
    property bool showCancelButton: true
    property bool deleteOnClose: true
    
    // ==================== Internal Props 内部属性 ====================
    property Item targetItem: null
    property bool isOpen: false
    readonly property int _sheetRadius: Enums.surfaceRadius(Enums.radius.large)
    readonly property color _sheetBackground: Enums.cardColor
    readonly property real _sheetBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color _sheetBorderColor: Enums.stateColor.dialogBorder
    readonly property color _sheetDividerColor: Enums.stateColor.borderLight

    // ==================== Signals 信号 ====================
    signal accepted()
    signal rejected()

    // ==================== Public Methods 公开方法 ====================
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

    width: contentContainer.width + 32
    height: contentContainer.height + buttonRow.height + 48
    visible: false
    flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoFluentShadowWindowHint
    color: Enums.transparent

    onActiveFocusItemChanged: {
        if (!activeFocusItem && isOpen) close()
    }

    // ==================== Content 内容 ====================
    // Fluent: 模糊阴影; neo: 硬阴影
    RectangularShadow {
        anchors.fill: container
        radius: container.radius
        color: Enums.shadow.level8.color
        blur: Enums.shadow.level8.blur
        offset.x: 0
        offset.y: Enums.shadow.level8.offset
        visible: Enums.usesSoftElevation
    }

    NeoShadow {
        target: container
        visible: Enums.isNeobrutalism
        z: container.z - 1
    }

    // Main container 主容器
    Rectangle {
        id: container
        anchors.fill: parent
        anchors.margins: Enums.spacing.m
        radius: control._sheetRadius
        color: control._sheetBackground
        border.width: control._sheetBorderWidth
        border.color: control._sheetBorderColor

        TicketPaper {
            anchors.fill: parent
        }
        
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
            lineColor: control._sheetDividerColor
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

}
