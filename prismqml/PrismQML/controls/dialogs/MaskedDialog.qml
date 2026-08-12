// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../.."
import "../../effects"

// MaskedDialog - Dialog with a translucent mask layer 带半透明遮罩层的对话框
//
// Architecture: Fill parent window, place dialogBody in center 架构：填满父窗口，中心放置 dialogBody
// 半透明遮罩铺满父窗口 + 居中主体带柔和投影 + 打开/关闭淡入淡出过渡,具体视觉参数见下方实现

OverlayDialogCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Dialog body content 对话框主体内容
    default property alias bodyContent: dialogBody.data

    // Dialog body reference 对话框主体引用
    readonly property alias body: dialogBody

    readonly property int _dialogRadius: Enums.surfaceRadius(Enums.radius.dialog)
    readonly property color _dialogBackground: Enums.hasOutlinedSurfaces ? Enums.dialogColor : Enums.dialogColors.containerBg
    readonly property int _dialogBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color _dialogBorderColor: Enums.hasOutlinedSurfaces ? Enums.borderColor : Enums.stateColor.dialogBorder
    readonly property color _dialogShadowColor: Enums.shadow.level16.color
    readonly property real _dialogShadowBlur: Enums.shadow.level16.blur
    readonly property real _dialogShadowOffset: Enums.shadow.level16.offset

    // ==================== Internal Methods 内部方法 ====================
    // Reset dialogBody position before opening 打开前重置 dialogBody 位置
    function _prepareOpen() {
        dialogBody.anchors.centerIn = Qt.binding(function() { return control })
    }

    // ==================== Content 内容 ====================
    // Shadow: soft drop shadow under the dialog body 主体下方柔和投影
    // Fluent: 模糊阴影; neo: 硬阴影
    RectangularShadow {
        anchors.fill: dialogBody
        radius: control._dialogRadius
        color: control._dialogShadowColor
        blur: control._dialogShadowBlur
        offset.x: 0
        offset.y: control._dialogShadowOffset
        visible: Enums.usesSoftElevation
    }

    NeoShadow {
        target: dialogBody
        visible: Enums.isNeobrutalism
        radius: control._dialogRadius
        z: dialogBody.z - 1
    }

    // Dialog body 对话框主体
    Rectangle {
        id: dialogBody
        objectName: "dialogBody"
        anchors.centerIn: parent

        // Default size, will be overridden by child 默认尺寸，由子类覆盖
        width: Enums.controlSize.dialogDefaultWidth
        height: Enums.controlSize.dialogDefaultHeight

        radius: control._dialogRadius

        // neo: 白面+黑边; Prism: overlay; Fluent: dialogColors
        color: control._dialogBackground

        border.width: control._dialogBorderWidth
        border.color: control._dialogBorderColor
        // Clip children to rounded corners 裁剪子元素以适应圆角
        clip: true
        
        // Animation 动画
        scale: control._isOpen ? 1 : 0.95
        opacity: control._isOpen ? 1 : 0

        TicketPaper {
            anchors.fill: parent
        }
        
        Behavior on scale {
            NumberAnimation {
                duration: control._isClosing ? Enums.duration.fast : Enums.duration.medium
                easing.type: control._isClosing ? Easing.Linear : Easing.InSine
            }
        }
        Behavior on opacity {
            NumberAnimation {
                duration: control._isClosing ? Enums.duration.fast : Enums.duration.medium
                easing.type: control._isClosing ? Easing.Linear : Easing.InSine
                onRunningChanged: {
                    if (!running && control._isClosing) {
                        control._isClosing = false
                        control.closed()
                    }
                }
            }
        }
        
        // Drag handler 拖拽处理
        MouseArea {
            property point dragStart

            anchors.fill: parent
            enabled: control.draggable
            drag.target: control.draggable ? dialogBody : null

            onPressed: (mouse) => {
                if (control.draggable) {
                    // Unbind anchors 解除锚点绑定
                    dialogBody.anchors.centerIn = undefined
                    dragStart = Qt.point(mouse.x, mouse.y)
                }
            }

            onPositionChanged: (mouse) => {
                if (pressed && control.draggable) {
                    var newX = dialogBody.x + mouse.x - dragStart.x
                    var newY = dialogBody.y + mouse.y - dragStart.y
                    // Clamp to parent bounds 限制在父组件范围内
                    dialogBody.x = Math.max(0, Math.min(newX, control.width - dialogBody.width))
                    dialogBody.y = Math.max(0, Math.min(newY, control.height - dialogBody.height))
                }
            }
        }
    }
}
