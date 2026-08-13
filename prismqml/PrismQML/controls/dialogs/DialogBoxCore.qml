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
    
    // ==================== Public Props 公开属性 ====================
    
    property bool actionsVisible: true      // Show action row 显示动作按钮区
    property Component footer: null             // Footer button component 按钮组件（由子类提供）

    // Explicit content width 显式内容宽度
    // When > 0, the dialog width is driven by this value instead of the content's
    // childrenRect. Set it when the body's root item already has a fixed width, to
    // avoid the implicitWidth<->childrenRect binding loop (childrenRect grows/oscillates
    // when a child overflows the fixed-width root). Leave -1 to keep the legacy
    // content-measured behavior (for bodies that must size to their content).
    // 大于 0 时对话框宽度由它决定，而非内容 childrenRect；当主体根项已固定宽度时设置它，
    // 以规避 implicitWidth<->childrenRect 绑定循环（子项溢出定宽根项会使 childrenRect
    // 变大/抖动）。保持 -1 则维持按内容测量的旧行为（供需随内容自适应的主体）。
    property int contentWidth: -1

    // Body content 主体内容
    default property alias bodyContent: bodyLayout.data

    // ==================== Readonly State 只读状态 ====================
    readonly property int _dialogRadius: Enums.surfaceRadius(Enums.radius.dialog)
    readonly property color _dialogBackground: Enums.dialogColor
    readonly property real _dialogBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color _dialogBorderColor: Enums.stateColor.dialogBorder
    readonly property color _dialogMaskColor: Enums.stateColor.dialogOverlay
    readonly property color _actionsRowBackground: Enums.stateColor.actionsRowBg
    readonly property color _dialogShadowColor: Enums.shadow.level16.color
    readonly property real _dialogShadowBlur: Enums.shadow.level16.blur
    readonly property real _dialogShadowOffset: Enums.shadow.level16.offset

    // ==================== Public Methods 公开方法 ====================

    // Validate form data before close 关闭前验证表单数据
    function validate() {
        return true
    }

    // Override accept to emit accepted 重写 accept 以发送 accepted
    function accept() {
        if (!_isOpen) return
        accepted()
        close()
    }

    // Override reject to emit rejected 重写 reject 以发送 rejected
    function reject() {
        if (!_isOpen) return
        rejected()
        close()
    }

    // ==================== Internal Methods 内部方法 ====================

    // Reset dialog body position before opening 打开前重置对话框位置
    function _prepareOpen() {
        dialogBodyContainer.anchors.horizontalCenter = Qt.binding(function() { return control.horizontalCenter })
        dialogBodyContainer.anchors.verticalCenter = Qt.binding(function() { return control.verticalCenter })
    }

    // Keep the complete dialog body inside the overlay bounds 保持对话框完整位于遮罩范围内
    function _setBoundedDialogPosition(candidateX, candidateY) {
        var maximumX = Math.max(0, control.width - dialogBodyContainer.width)
        var maximumY = Math.max(0, control.height - dialogBodyContainer.height)
        dialogBodyContainer.x = Math.max(0, Math.min(candidateX, maximumX))
        dialogBodyContainer.y = Math.max(0, Math.min(candidateY, maximumY))
    }

    // ==================== Content 内容 ====================
    maskColor: control._dialogMaskColor

    // Dialog body 对话框主体
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
            color: control._dialogShadowColor
            blur: control._dialogShadowBlur
            offset.x: 0
            offset.y: control._dialogShadowOffset
            opacity: dialogBody.opacity
            scale: dialogBody.scale
            visible: Enums.usesSoftElevation && !Enums.isNeumorphism
        }

        NeumorphicShadow {
            target: dialogBody
            visible: Enums.isNeumorphism
            opacity: dialogBody.opacity
            scale: dialogBody.scale
            transformOrigin: dialogBody.transformOrigin
            z: dialogBody.z - 1
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
            radius: control._dialogRadius
            clip: true  // Clip children to rounded corners 裁剪子元素以适应圆角

            // Background color 背景色
            color: control._dialogBackground

            // Border 边框
            border.width: control._dialogBorderWidth
            border.color: control._dialogBorderColor
            // Animation 动画
            scale: control._isOpen ? 1 : 0.9
            opacity: control._isOpen ? 1 : 0

            TicketPaper {
                anchors.fill: parent
            }
            
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
            
            // ==================== Content 内容 ====================
            // Prevent click events from propagating to mask layer 阻止点击事件传播到遮罩层
            // Also clear input focus when clicking blank area 同时在点击空白处清除输入焦点
            MouseArea {
                anchors.fill: parent
                z: Enums.zIndex.base  // Below content 在内容层之下
                onClicked: parent.forceActiveFocus()
            }

            // Drag handler stays below body content so interactive child cursors
            // and clicks keep precedence. 拖拽层位于正文内容下方，确保交互子项的光标和点击优先。
            MouseArea {
                property point dragStart

                anchors.fill: bodyLayout
                enabled: control.draggable
                propagateComposedEvents: true

                onPressed: (mouse) => {
                    dragStart = Qt.point(mouse.x, mouse.y)
                    mouse.accepted = control.draggable
                }

                onPositionChanged: (mouse) => {
                    if (pressed && control.draggable) {
                        dialogBodyContainer.anchors.horizontalCenter = undefined
                        dialogBodyContainer.anchors.verticalCenter = undefined
                        var candidateX = dialogBodyContainer.x + mouse.x - dragStart.x
                        var candidateY = dialogBodyContainer.y + mouse.y - dragStart.y
                        control._setBoundedDialogPosition(candidateX, candidateY)
                    }
                }
            }
            
            // View layout 视图布局
            Item {
                id: bodyLayout
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: actionsRow.top
                anchors.margins: Enums.spacing.xxxl
                
                // Prefer the explicit contentWidth to break the childrenRect binding loop;
                // fall back to childrenRect when unset (contentWidth <= 0).
                // 优先用显式 contentWidth 以打断 childrenRect 绑定循环；未设置(<=0)时回退 childrenRect。
                implicitWidth: control.contentWidth > 0 ? control.contentWidth : childrenRect.width
                implicitHeight: childrenRect.height
            }
            
            // Button group 按钮组
            Rectangle {
                id: actionsRow
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: control.actionsVisible ? Enums.dialog.actionsRowHeight : 0
                visible: control.actionsVisible
                
                // Background color 背景色
                color: control._actionsRowBackground
                
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
