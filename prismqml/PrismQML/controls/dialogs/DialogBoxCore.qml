// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../.."
import "../../effects"
import "../buttons/Button"

// DialogBoxCore - Customizable dialog box base class 可定制对话框基类
OverlayDialogCore {
    id: control
    
    // Override mask color for dialog 对话框使用不同的遮罩颜色
    maskColor: Enums.stateColor.dialogOverlay
    
    property bool actionsVisible: true      // Show action row 显示动作按钮区
    property Component footer: null             // Footer button component 按钮组件（由子类提供）

    // Body content 主体内容
    default property alias bodyContent: bodyLayout.data

    // ==================== Override Methods 重写方法 ====================

    // Validate form data before close 关闭前验证表单数据
    function validate() {
        return true
    }

    // Override accept to emit accepted 重写 accept 以发送 accepted
    function accept() {
        accepted()
        close()
    }

    // Override reject to emit rejected 重写 reject 以发送 rejected
    function reject() {
        rejected()
        close()
    }

    // Override open to reset dialogBody position 重写 open 以重置位置
    function open() {
        // Save original parent 保存原始父组件
        if (!_originalParent) {
            _originalParent = control.parent
        }

        // Determine overlay target 确定覆盖目标
        var target = _resolveOverlayTarget()
        if (target && target !== control.parent) {
            control.parent = target
        }

        // Reset position 重置位置
        dialogBodyContainer.anchors.horizontalCenter = Qt.binding(function() { return control.horizontalCenter })
        dialogBodyContainer.anchors.verticalCenter = Qt.binding(function() { return control.verticalCenter })
        _isOpen = true
    }

    // ==================== Dialog Body 对话框主体 ====================
    Item {
        id: dialogBodyContainer
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        width: dialogBody.width
        height: dialogBody.height
        
        // Shadow effect using RectangularShadow 使用RectangularShadow实现阴影
        // Fluent: 模糊浮层阴影; Neobrutalism: 硬阴影(NeoShadow), 跟随对话框开合 opacity/scale。
        RectangularShadow {
            anchors.fill: dialogBody
            radius: dialogBody.radius
            color: Enums.shadow.level8.color
            blur: Enums.shadow.level8.blur
            offset: Qt.vector2d(0, Enums.shadow.level8.offset)
            opacity: dialogBody.opacity
            scale: dialogBody.scale
            visible: !Enums.isNeobrutalism
        }

        NeoShadow {
            target: dialogBody
            visible: Enums.isNeobrutalism
            opacity: dialogBody.opacity
            scale: dialogBody.scale
            transformOrigin: dialogBody.transformOrigin
            z: dialogBody.z - 1
        }

        Rectangle {
            id: dialogBody
            anchors.fill: parent
            radius: Enums.radius.dialog
            clip: true  // Clip children to rounded corners 裁剪子元素以适应圆角

            // Background color 背景色
            color: Enums.dialogColor

            // Border 边框
            border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
            border.color: Enums.stateColor.dialogBorder
            
            // Animation 动画
            scale: control._isOpen ? 1 : 0.9
            opacity: control._isOpen ? 1 : 0
            
            Behavior on scale { 
                NumberAnimation { 
                    duration: Enums.duration.medium
                    easing.type: control._isClosing ? Easing.InBack : Easing.OutBack
                } 
            }
            Behavior on opacity { 
                NumberAnimation { 
                    duration: Enums.duration.medium
                    onRunningChanged: {
                        // Hide after close animation finishes 关闭动画完成后隐藏
                        if (!running && control._isClosing) {
                            control._isClosing = false
                        }
                    }
                } 
            }
            
            // ==================== Event Blocker 事件阻止层 ====================
            // Prevent click events from propagating to mask layer 阻止点击事件传播到遮罩层
            // Also clear input focus when clicking blank area 同时在点击空白处清除输入焦点
            MouseArea {
                anchors.fill: parent
                z: Enums.zIndex.base  // Below content 在内容层之下
                onClicked: parent.forceActiveFocus()
            }
            
            // ==================== View Layout 视图布局 ====================
            Item {
                id: bodyLayout
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: actionsRow.top
                anchors.margins: Enums.spacing.xxxl
                
                implicitWidth: childrenRect.width
                implicitHeight: childrenRect.height
            }
            
            // ==================== Button Group 按钮组 ====================
            Rectangle {
                id: actionsRow
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: control.actionsVisible ? Enums.dialog.actionsRowHeight : 0
                visible: control.actionsVisible
                
                // Background color 背景色
                color: Enums.stateColor.actionsRowBg
                
                // Top border 顶部边框
                Separator {
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.right: parent.right
                }
                
                // Footer button area 按钮区域（由子类通过 footer 属性提供）
                Loader {
                    id: footerLoader
                    anchors.centerIn: parent
                    active: control.footer !== null
                    sourceComponent: control.footer
                    // 注入 dialog 引用，自定义组件声明 property var dialog 即可接收
                    onLoaded: {
                        if (item && item.hasOwnProperty("dialog")) {
                            item.dialog = control
                        }
                    }
                }
            }
            
            // Drag handler 拖拽处理
            MouseArea {
                anchors.fill: bodyLayout
                enabled: control.draggable
                propagateComposedEvents: true
                
                property point dragStart
                
                onPressed: (mouse) => {
                    dragStart = Qt.point(mouse.x, mouse.y)
                    mouse.accepted = control.draggable
                }
                
                onPositionChanged: (mouse) => {
                    if (pressed && control.draggable) {
                        dialogBodyContainer.anchors.horizontalCenter = undefined
                        dialogBodyContainer.anchors.verticalCenter = undefined
                        dialogBodyContainer.x += mouse.x - dragStart.x
                        dialogBodyContainer.y += mouse.y - dragStart.y
                    }
                }
            }
        }
    }
    
    // Binding for dialogBody size 绑定 dialogBody 尺寸
    Binding {
        target: dialogBodyContainer
        property: "width"
        value: Math.max(Enums.dialog.minWidth, bodyLayout.implicitWidth + Enums.dialog.contentPadding)
    }
    Binding {
        target: dialogBodyContainer
        property: "height"
        value: bodyLayout.implicitHeight + actionsRow.height + Enums.dialog.contentPadding
    }

}
